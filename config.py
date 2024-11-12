import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://admin:admin@localhost/previanza'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'mail.vaporcigarrillos.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'paul@vaporcigarrillos.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'Videogames.2017'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'paul@vaporcigarrillos.com'

    # Password reset token expiration
    PASSWORD_RESET_EXPIRATION = timedelta(hours=1)

    # Debug mode for development
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Asegurarse de que la carpeta migrations existe
    if not os.path.exists('migrations'):
        os.makedirs('migrations')
