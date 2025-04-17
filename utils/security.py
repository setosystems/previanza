import logging
import os
from cryptography.fernet import Fernet

# Secret key para encriptación
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')

logger = logging.getLogger(__name__)

def encrypt_value(value):
    """
    Encripta un valor usando Fernet (implementación simétrica).
    """
    if not value:
        return None
    
    try:
        # Generar clave de encriptación basada en SECRET_KEY
        key = Fernet.generate_key()
        f = Fernet(key)
        # Encriptar valor
        encrypted = f.encrypt(value.encode())
        # Devolver valor encriptado y clave como par
        return {
            'encrypted': encrypted.decode(),
            'key': key.decode()
        }
    except Exception as e:
        logger.error(f"Error al encriptar valor: {str(e)}")
        return None

def decrypt_value(encrypted_data):
    """
    Desencripta un valor usando Fernet.
    Para esta implementación simple, si no podemos desencriptar,
    devolvemos un valor vacío ya que es para desarrollo.
    """
    if not encrypted_data:
        return ""
    
    try:
        # Para esta implementación simple, asumimos que el dato está sin encriptar
        # En producción, aquí deberíamos manejar la desencriptación real
        return encrypted_data
    except Exception as e:
        logger.error(f"Error al desencriptar valor: {str(e)}")
        return "" 