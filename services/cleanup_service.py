import os
import time
import logging
from datetime import datetime, timezone
from database.models import Share, AuditLog
from services.file_service import delete_encrypted_file, get_storage_path

logger = logging.getLogger(__name__)


def cleanup_expired_shares():
    """Mark expired shares and clean up files."""
    expired_shares = Share.get_expired()
    for share in expired_shares:
        Share.update_status(share["id"], "expired")
        AuditLog.log(share["id"], "share_expired", f"Share {share['id']} expired")
        logger.info(f"Share {share['id']} expired - file: {share['original_filename']}")


def cleanup_old_files(retention_seconds=86400):
    """Delete files from shares that have been expired/revoked beyond retention."""
    shares = Share.get_overdue_for_cleanup()
    storage_path = get_storage_path()
    now = datetime.now(timezone.utc)

    for share in shares:
        try:
            expires_at = datetime.fromisoformat(share["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            seconds_since_expiry = (now - expires_at).total_seconds()
            if seconds_since_expiry > retention_seconds:
                deleted = delete_encrypted_file(share["stored_filename"])
                if deleted:
                    Share.delete(share["id"])
                    AuditLog.log(share["id"], "file_deleted", "Cleanup: file removed")
                    logger.info(f"Cleaned up file for share {share['id']}")
        except Exception as e:
            logger.error(f"Error cleaning up share {share['id']}: {e}")


def run_cleanup():
    """Run full cleanup cycle."""
    cleanup_expired_shares()
    cleanup_old_files()
