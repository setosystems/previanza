import logging
import click
from flask import Flask, render_template, redirect, url_for, send_from_directory, flash, jsonify, session
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config, basedir
from models import DocumentType, db, User, UserRole, Policy, Commission, Client, Product, SMTPConfig
from utils.security import decrypt_value
from sqlalchemy.exc import OperationalError
import time
from extensions import mail
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from sqlalchemy.sql import text

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()  # Cargar variables de entorno desde .env

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)
    
    # Configurar sesiones persistentes basadas en cookies
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Cargar configuración SMTP desde la base de datos
    with app.app_context():
        try:
            # Verificar si la tabla existe
            db.session.execute(text('SELECT 1 FROM information_schema.tables WHERE table_name = \'smtp_config\''))
            smtp_config = SMTPConfig.get_active_config()
            if smtp_config:
                app.config.update({
                    'MAIL_SERVER': smtp_config.mail_server,
                    'MAIL_PORT': smtp_config.mail_port,
                    'MAIL_USE_TLS': smtp_config.mail_use_tls,
                    'MAIL_USE_SSL': smtp_config.mail_use_ssl,
                    'MAIL_USERNAME': smtp_config.mail_username,
                    'MAIL_PASSWORD': decrypt_value(smtp_config.mail_password),
                    'MAIL_DEFAULT_SENDER': smtp_config.mail_default_sender
                })
                logging.info("SMTP configuration loaded from database")
        except Exception as e:
            logging.info("Using default SMTP configuration from config.py")
    
    mail.init_app(app)

    # Configure login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes import auth, clients, policies, products, agents, reports, config
    app.register_blueprint(auth.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(policies.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(agents.bp)
    app.register_blueprint(reports.bp, url_prefix='/reports')
    app.register_blueprint(config.bp)

    # Rutas principales
    @app.route('/')
    def index():
        # Redirigir a login si no está autenticado
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        try:
            # Obtener fechas para filtrado
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            previous_start = start_date - timedelta(days=30)

            # Definir variables con valores predeterminados antes de cualquier consulta
            total_policies = 0
            total_premium = 0
            total_commissions = 0
            active_clients = 0
            new_clients = 0
            policy_growth = 0
            weekly_activity = {'dates': [], 'counts': []}
            sales_data = {'dates': [], 'totals': []}
            products_performance_list = []
            top_clients_list = []
            top_agents_list = []

            # Estadísticas generales
            total_policies = Policy.query.count() or 0
            total_premium_raw = db.session.query(func.sum(Policy.premium)).scalar() or 0
            total_premium = float(total_premium_raw)
            
            total_commissions_raw = db.session.query(func.sum(Commission.amount)).scalar() or 0
            total_commissions = float(total_commissions_raw)
            
            # Cálculo de crecimiento de pólizas
            current_period_policies = Policy.query.filter(
                Policy.solicitation_date.between(start_date, end_date)
            ).count()
            previous_period_policies = Policy.query.filter(
                Policy.solicitation_date.between(previous_start, start_date)
            ).count()
            
            # Asegurar que policy_growth siempre tenga un valor, incluso si previous_period_policies es 0
            try:
                policy_growth = (
                    ((current_period_policies - previous_period_policies) / previous_period_policies * 100)
                    if previous_period_policies > 0 else 0
                )
            except Exception as e:
                logging.error(f"Error calculando policy_growth: {str(e)}")
                policy_growth = 0

            # Clientes activos y nuevos
            active_clients = Client.query.count()
            new_clients = Client.query.filter(
                Client.id.in_(
                    db.session.query(Policy.client_id).filter(
                        Policy.solicitation_date.between(start_date, end_date)
                    )
                )
            ).count()

            # Actividad semanal
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            daily_counts = db.session.query(
                func.date_trunc('day', Policy.solicitation_date).label('day'),
                func.count(Policy.id).label('count')
            ).filter(
                Policy.solicitation_date >= week_start
                # Sin filtrar por estado para mostrar todas las pólizas
            ).group_by('day').all()

            # Crear diccionario con los días de la semana en orden correcto
            days_of_week = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
            weekly_activity_temp = {day: 0 for day in days_of_week}
            
            # Llenar con datos reales
            for day_data in daily_counts:
                day_abbr = day_data.day.strftime('%a')[0]
                # Corrección para algunos sistemas que pueden devolver abreviaturas en inglés
                if day_abbr == 'W':  # Wednesday en inglés
                    day_abbr = 'X'
                elif day_abbr == 'T':  # Tuesday o Thursday en inglés
                    weekday = day_data.day.weekday()
                    day_abbr = 'M' if weekday == 1 else 'J'  # 1 es martes, 3 es jueves
                
                if day_abbr in weekly_activity_temp:
                    weekly_activity_temp[day_abbr] = int(day_data.count)
            
            # Formato compatible con el gráfico - asegurar el orden correcto
            weekly_activity = {
                'dates': days_of_week,
                'counts': [int(weekly_activity_temp[day]) for day in days_of_week]
            }

            # Ventas diarias
            daily_sales = db.session.query(
                func.date_trunc('day', Policy.solicitation_date).label('date'),
                func.sum(Policy.premium).label('total')
            ).filter(
                Policy.solicitation_date.between(start_date, end_date)
            ).group_by('date').order_by('date').all()

            sales_data = {
                'dates': [d.date.strftime('%d/%m') for d in daily_sales],
                'totals': [float(d.total) if d.total else 0 for d in daily_sales]
            }

            # Rendimiento de productos
            products_query = db.session.query(
                Product.id,
                Product.name,
                Product.description,
                Product.image_url,
                func.count(Policy.id).label('policy_count'),
                func.sum(Policy.premium).label('total_premium')
            ).outerjoin(
                Policy, 
                db.and_(
                    Policy.product_id == Product.id,
                    Policy.solicitation_date.between(start_date, end_date)
                )
            ).group_by(Product.id, Product.name, Product.description, Product.image_url)\
            .order_by(func.sum(Policy.premium).desc())\
            .all()
            
            # Convertir objetos Row a diccionarios para evitar problemas de serialización JSON
            products_performance_list = []
            for p in products_query:
                # Verificar si total_premium es None y convertir a 0 si es necesario
                premium = 0
                if p.total_premium is not None:
                    premium = float(p.total_premium)
                
                # Verificar si policy_count es None y convertir a 0 si es necesario
                count = 0
                if p.policy_count is not None:
                    count = int(p.policy_count)
                
                products_performance_list.append({
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'image_url': p.image_url,
                    'policy_count': count,
                    'total_premium': premium
                })

            # Top clientes
            top_clients = db.session.query(
                Client.name,
                func.count(Policy.id).label('policy_count'),
                func.sum(Policy.premium).label('total_premium')
            ).join(Policy).group_by(Client.id, Client.name)\
            .order_by(func.sum(Policy.premium).desc())\
            .limit(5).all()
            
            # Convertir a diccionarios
            top_clients_list = []
            for c in top_clients:
                top_clients_list.append({
                    'name': c.name,
                    'policy_count': c.policy_count or 0,
                    'total_premium': float(c.total_premium) if c.total_premium else 0
                })

            # Top agentes
            top_agents = db.session.query(
                User.name,
                func.count(Policy.id).label('policy_count'),
                func.sum(Policy.premium).label('total_premium')
            ).join(Policy, User.id == Policy.agent_id)\
            .filter(User.role == UserRole.AGENTE)\
            .group_by(User.id, User.name)\
            .order_by(func.sum(Policy.premium).desc())\
            .limit(5).all()
            
            # Convertir a diccionarios
            top_agents_list = []
            for a in top_agents:
                top_agents_list.append({
                    'name': a.name,
                    'policy_count': a.policy_count or 0,
                    'total_premium': float(a.total_premium) if a.total_premium else 0
                })

            return render_template('index.html',
                total_policies=total_policies,
                total_premium=total_premium,
                total_commissions=total_commissions,
                active_clients=active_clients,
                new_clients=new_clients,
                policy_growth=policy_growth,
                weekly_activity=weekly_activity,
                daily_sales=sales_data,
                products_performance=products_performance_list,
                top_clients=top_clients_list,
                top_agents=top_agents_list
            )

        except Exception as e:
            logging.error(f"Error en dashboard: {str(e)}")
            flash('Error al cargar el dashboard', 'error')
            
            # Proporcionar valores predeterminados para todas las variables requeridas por la plantilla
            return render_template('index.html',
                error=True,
                total_policies=0,
                total_premium=0,
                total_commissions=0,
                active_clients=0,
                new_clients=0,
                policy_growth=0,
                weekly_activity={'dates': [], 'counts': []},
                daily_sales={'dates': [], 'totals': []},
                products_performance=[],
                top_clients=[],
                top_agents=[]
            )

    @app.errorhandler(401)
    def unauthorized(error):
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    @app.context_processor
    def inject_user_role():
        return {
            'user_role': current_user.role if current_user.is_authenticated else None,
            'UserRole': UserRole
        }

    # Comando para crear usuario administrador
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("email")
    @click.argument("password")
    def create_admin(username, email, password):
        """Crea un usuario administrador."""
        with app.app_context():
            admin_user = User.query.filter_by(username=username).first()
            if admin_user is None:
                admin_user = User(
                    username=username,
                    email=email,
                    role=UserRole.ADMIN,
                    document_type=DocumentType.DNI,
                    document_number="12345678"
                )
                admin_user.set_password(password)
                db.session.add(admin_user)
                db.session.commit()
                print(f"Usuario administrador '{username}' creado.")
            else:
                return 0  # Silenciosamente indica éxito si el usuario ya existe

    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

    # Agregar funciones globales a Jinja2
    app.jinja_env.globals.update(min=min)

    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"}), 200

    return app

app = create_app()

def verify_database():
    """Verifica y crea las tablas de la base de datos si no existen."""
    if os.environ.get('FLASK_APP_WORKER_ID') == '1':  # Solo el primer worker
        with app.app_context():
            try:
                db.create_all()
                if os.environ.get('FLASK_DEBUG') == '1':
                    logging.info("Base de datos verificada exitosamente")
            except Exception as e:
                logging.error(f"Error al verificar la base de datos: {str(e)}")

if not app.debug:
    # Compilar Tailwind CSS
    import subprocess
    subprocess.run([
        'npx', 
        'tailwindcss', 
        '-i', 
        'static/css/input.css', 
        '-o', 
        'static/css/output.css', 
        '--minify',
        '--quiet'
    ], capture_output=True)

# Verificar la base de datos al inicio
verify_database()

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=5000, debug=True)
