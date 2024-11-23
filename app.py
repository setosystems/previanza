import logging
import click
from flask import Flask, render_template, redirect, url_for, send_from_directory, flash
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config, basedir
from models import DocumentType, db, User, UserRole, Policy, Commission, Client, Product
from sqlalchemy.exc import OperationalError
import time
from extensions import mail
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.sql import func

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()  # Cargar variables de entorno desde .env

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
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

            # Estadísticas generales
            total_policies = Policy.query.count()
            total_premium = db.session.query(func.sum(Policy.premium)).scalar() or 0
            total_commissions = db.session.query(func.sum(Commission.amount)).scalar() or 0
            
            # Cálculo de crecimiento de pólizas
            current_period_policies = Policy.query.filter(
                Policy.start_date.between(start_date, end_date)
            ).count()
            previous_period_policies = Policy.query.filter(
                Policy.start_date.between(previous_start, start_date)
            ).count()
            policy_growth = (
                ((current_period_policies - previous_period_policies) / previous_period_policies * 100)
                if previous_period_policies > 0 else 0
            )

            # Clientes activos y nuevos
            active_clients = Client.query.count()
            new_clients = Client.query.filter(
                Client.id.in_(
                    db.session.query(Policy.client_id).filter(
                        Policy.start_date.between(start_date, end_date)
                    )
                )
            ).count()

            # Actividad semanal
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            daily_counts = db.session.query(
                func.date_trunc('day', Policy.start_date).label('day'),
                func.count(Policy.id).label('count')
            ).filter(
                Policy.start_date >= week_start
            ).group_by('day').all()

            weekly_activity = {
                'L': 0, 'M': 0, 'X': 0, 'J': 0, 'V': 0, 'S': 0, 'D': 0
            }
            for day_data in daily_counts:
                weekly_activity[day_data.day.strftime('%a')[0]] = day_data.count

            # Ventas diarias
            daily_sales = db.session.query(
                func.date_trunc('day', Policy.start_date).label('date'),
                func.sum(Policy.premium).label('total')
            ).filter(
                Policy.start_date.between(start_date, end_date)
            ).group_by('date').order_by('date').all()

            sales_data = {
                'dates': [d.date.strftime('%d/%m') for d in daily_sales],
                'totals': [float(d.total) if d.total else 0 for d in daily_sales]
            }

            # Rendimiento de productos
            products_performance = db.session.query(
                Product.name,
                Product.description,
                Product.image_url,
                func.count(Policy.id).label('policy_count'),
                func.sum(Policy.premium).label('total_premium')
            ).outerjoin(
                Policy, 
                db.and_(
                    Policy.product_id == Product.id,
                    Policy.start_date.between(start_date, end_date)
                )
            ).group_by(Product.id, Product.name, Product.description, Product.image_url)\
            .order_by(func.sum(Policy.premium).desc())\
            .all()

            # Top clientes
            top_clients = db.session.query(
                Client.name,
                func.count(Policy.id).label('policy_count'),
                func.sum(Policy.premium).label('total_premium')
            ).join(Policy).group_by(Client.id, Client.name)\
            .order_by(func.sum(Policy.premium).desc())\
            .limit(5).all()

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

            return render_template('index.html',
                total_policies=total_policies,
                total_premium=total_premium,
                total_commissions=total_commissions,
                active_clients=active_clients,
                new_clients=new_clients,
                policy_growth=policy_growth,
                weekly_activity=weekly_activity,
                daily_sales=sales_data,
                products_performance=products_performance,
                top_clients=top_clients,
                top_agents=top_agents
            )

        except Exception as e:
            logging.error(f"Error en dashboard: {str(e)}")
            flash('Error al cargar el dashboard', 'error')
            return render_template('index.html', error=True)

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
            if User.query.filter_by(username=username).first():
                print("El nombre de usuario ya existe.")
                return
            if User.query.filter_by(email=email).first():
                print("El correo electrónico ya está en uso.")
                return
            
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

    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

    return app

app = create_app()

# Crear todas las tablas solo si no existen
with app.app_context():
    try:
        db.create_all()
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
        '--minify'
    ])

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=5000, debug=True)
