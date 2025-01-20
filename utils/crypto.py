from cryptography.fernet import Fernet
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key():
    """
    Obtiene o genera una clave de encriptación.
    La clave se deriva de una variable de entorno SECRET_KEY usando PBKDF2.
    """
    secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
    
    # Usar PBKDF2 para derivar una clave segura
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'smtp-config-salt',  # Salt fijo para consistencia
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key

def encrypt_value(value):
    """
    Encripta un valor usando Fernet.
    """
    if not value:
        return None
    
    f = Fernet(get_encryption_key())
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value):
    """
    Desencripta un valor usando Fernet.
    """
    if not encrypted_value:
        return None
    
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_value.encode()).decode() 