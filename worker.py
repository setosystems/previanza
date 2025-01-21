from app import create_app
from rq import Worker
from extensions import redis_conn, mail
import time
from sqlalchemy.exc import OperationalError
import logging
from sqlalchemy import text
from utils.crypto import verify_value

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(app):
    """Espera a que la base de datos esté disponible."""
    logger.info("Esperando a que la base de datos esté lista...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                # Intenta hacer una consulta simple
                from models import db
                db.session.execute(text('SELECT 1'))
                logger.info("Base de datos lista")
                return True
        except OperationalError:
            retry_count += 1
            time.sleep(1)
    
    raise Exception("No se pudo conectar a la base de datos después de 30 intentos")

def verify_smtp_config(app):
    """Verifica que exista una configuración SMTP activa y la aplica."""
    try:
        with app.app_context():
            from models import SMTPConfig
            smtp_config = SMTPConfig.get_active_config()
            
            if not smtp_config:
                logger.warning("No se encontró una configuración SMTP activa")
                return False

            logger.info("Configuración SMTP activa encontrada")

            # Actualizar la configuración de la aplicación
            app.config.update({
                'MAIL_SERVER': smtp_config.mail_server,
                'MAIL_PORT': smtp_config.mail_port,
                'MAIL_USE_TLS': smtp_config.mail_use_tls,
                'MAIL_USE_SSL': smtp_config.mail_use_ssl,
                'MAIL_USERNAME': smtp_config.mail_username,
                'MAIL_PASSWORD': smtp_config.mail_password,  # Usar el hash directamente
                'MAIL_DEFAULT_SENDER': smtp_config.mail_default_sender
            })

            # Reinicializar la extensión de mail con la nueva configuración
            try:
                mail.init_app(app)
                logger.info(f"Configuración SMTP actualizada: servidor={smtp_config.mail_server}, puerto={smtp_config.mail_port}")
                return True
            except Exception as e:
                logger.error(f"Error al inicializar la configuración SMTP: {str(e)}")
                return False

    except Exception as e:
        logger.error(f"Error al verificar la configuración SMTP: {str(e)}")
        return False

def wait_for_redis():
    """Espera a que Redis esté disponible."""
    logger.info("Esperando a Redis...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            redis_conn.ping()
            logger.info("Redis listo")
            return True
        except:
            retry_count += 1
            time.sleep(1)
    
    raise Exception("No se pudo conectar a Redis después de 30 intentos")

def main():
    try:
        app = create_app()
        
        # Esperar a que los servicios estén disponibles
        wait_for_db(app)
        wait_for_redis()
        
        # Verificar y aplicar configuración SMTP
        if not verify_smtp_config(app):
            logger.warning("El worker continuará con la configuración SMTP por defecto")
        
        with app.app_context():
            logger.info("Iniciando worker...")
            worker = Worker(['default'], connection=redis_conn)
            worker.work()
    except Exception as e:
        logger.error(f"Error fatal en el worker: {str(e)}")
        raise

if __name__ == "__main__":
    main() 