import os
from cryptography.fernet import Fernet
from typing import Optional

# Use an environment variable for the encryption key
# Generate one using Fernet.generate_key().decode() if not set
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Creating a fallback or warning (in production this should be mandatory)
    # For initial setup, we might want to log a warning or use a default (not recommended for prod)
    # Here we'll raise an error if not found in a real scenario, but for now we'll 
    # provide a way to work or instructions
    pass

def get_fernet() -> Fernet:
    """Initialize Fernet with the encryption key."""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set")
    return Fernet(key.encode())

def encrypt_token(token: str) -> str:
    """Encrypt a plain text token."""
    if not token:
        return ""
    f = get_fernet()
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token."""
    if not encrypted_token:
        return ""
    f = get_fernet()
    return f.decrypt(encrypted_token.encode()).decode()
