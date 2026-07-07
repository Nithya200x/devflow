import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT = os.getenv("TOKEN_ENCRYPTION_SALT", "devflow-token-encryption-salt").encode()

def _derive_key(master_key: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=600000)
    return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))

def encrypt_token(plain_token: str, master_key: str = None) -> str:
    if not plain_token:
        return ""
    key = _derive_key(master_key or os.getenv("TOKEN_ENCRYPTION_KEY", "devflow-default-enc-key"))
    f = Fernet(key)
    return f.encrypt(plain_token.encode()).decode()

def decrypt_token(encrypted_token: str, master_key: str = None) -> str:
    if not encrypted_token:
        return ""
    key = _derive_key(master_key or os.getenv("TOKEN_ENCRYPTION_KEY", "devflow-default-enc-key"))
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()
