import os
import hashlib
from pathlib import Path

DEFAULT_STORAGE = str(Path(__file__).resolve().parent.parent / "storage" / "encrypted")


def _get_storage_path():
    """Get storage path from Flask config or environment."""
    try:
        from flask import current_app
        return current_app.config.get("STORAGE_PATH", os.environ.get("STORAGE_PATH", DEFAULT_STORAGE))
    except (ImportError, RuntimeError):
        return os.environ.get("STORAGE_PATH", DEFAULT_STORAGE)


def ensure_storage_dir():
    os.makedirs(_get_storage_path(), exist_ok=True)


def get_storage_path():
    ensure_storage_dir()
    return _get_storage_path()


def save_encrypted_file(file_data, stored_filename):
    """Save encrypted file data to storage."""
    ensure_storage_dir()
    filepath = os.path.join(_get_storage_path(), stored_filename)
    with open(filepath, "wb") as f:
        f.write(file_data)
    return filepath


def get_encrypted_file_path(stored_filename):
    """Get path to stored encrypted file."""
    filepath = os.path.join(_get_storage_path(), stored_filename)
    if not os.path.exists(filepath):
        return None
    return filepath


def delete_encrypted_file(stored_filename):
    """Delete stored encrypted file."""
    filepath = os.path.join(_get_storage_path(), stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def compute_file_hash(data):
    """Compute SHA-256 hash of file data."""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def get_file_size(filepath):
    """Get file size in bytes."""
    return os.path.getsize(filepath)
