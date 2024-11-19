import logging
import click
from flask import Flask, render_template, redirect, url_for, send_from_directory
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config, basedir
from models import DocumentType, db, User, UserRole
from sqlalchemy.exc import OperationalError
import time
from extensions import mail
import os
from dotenv import load_dotenv

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
        # Si está autenticado, mostrar el dashboard
        return render_template('index.html')

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
