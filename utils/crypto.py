import logging
import bcrypt

logger = logging.getLogger(__name__)

def hash_value(value):
    """
    Genera un hash seguro de un valor usando bcrypt.
    """
    if not value:
        return None
    
    try:
        # Generar salt y hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(value.encode(), salt)
        return hashed.decode()
    except Exception as e:
        logger.error(f"Error al generar hash: {str(e)}")
        raise

def verify_value(value, hashed_value):
    """
    Verifica si un valor coincide con su hash.
    """
    if not value or not hashed_value:
        return False
    
    try:
        return bcrypt.checkpw(value.encode(), hashed_value.encode())
    except Exception as e:
        logger.error(f"Error al verificar hash: {str(e)}")
        return False 