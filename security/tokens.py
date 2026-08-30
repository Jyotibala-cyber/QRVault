import secrets
import hashlib


def generate_share_token():
    """Generate a cryptographically secure random token for sharing."""
    return secrets.token_urlsafe(32)


def generate_management_token():
    """Generate a separate management token for the uploader."""
    return secrets.token_urlsafe(32)


def hash_token(token):
    """Hash a token for secure database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_file_id():
    """Generate a random file identifier."""
    return secrets.token_hex(16)
