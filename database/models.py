from datetime import datetime, timezone
from database.db import get_db


class Share:
    @staticmethod
    def create(
        token_hash,
        management_token_hash,
        original_filename,
        stored_filename,
        file_size,
        mime_type,
        expires_at,
        max_downloads=3,
        password_hash=None,
        created_ip=None,
    ):
        db = get_db()
        cursor = db.execute(
            """INSERT INTO shares
               (token_hash, management_token_hash, original_filename, stored_filename,
                file_size, mime_type, expires_at, max_downloads, password_hash, created_ip)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                token_hash,
                management_token_hash,
                original_filename,
                stored_filename,
                file_size,
                mime_type,
                expires_at,
                max_downloads,
                password_hash,
                created_ip,
            ),
        )
        db.commit()
        share_id = cursor.lastrowid
        db.close()
        return share_id

    @staticmethod
    def find_by_token_hash(token_hash):
        db = get_db()
        share = db.execute(
            "SELECT * FROM shares WHERE token_hash = ?", (token_hash,)
        ).fetchone()
        db.close()
        return dict(share) if share else None

    @staticmethod
    def find_by_management_token(management_token_hash):
        db = get_db()
        share = db.execute(
            "SELECT * FROM shares WHERE management_token_hash = ?",
            (management_token_hash,),
        ).fetchone()
        db.close()
        return dict(share) if share else None

    @staticmethod
    def increment_download(share_id):
        db = get_db()
        db.execute(
            "UPDATE shares SET download_count = download_count + 1 WHERE id = ?",
            (share_id,),
        )
        db.commit()
        share = db.execute("SELECT * FROM shares WHERE id = ?", (share_id,)).fetchone()
        db.close()
        return dict(share) if share else None

    @staticmethod
    def revoke(share_id):
        db = get_db()
        db.execute(
            "UPDATE shares SET revoked = 1, status = 'revoked' WHERE id = ?",
            (share_id,),
        )
        db.commit()
        db.close()

    @staticmethod
    def delete(share_id):
        db = get_db()
        db.execute("DELETE FROM shares WHERE id = ?", (share_id,))
        db.commit()
        db.close()

    @staticmethod
    def get_expired():
        db = get_db()
        now = datetime.now(timezone.utc).isoformat()
        shares = db.execute(
            "SELECT * FROM shares WHERE expires_at < ? AND status != 'expired'",
            (now,),
        ).fetchall()
        db.close()
        return [dict(s) for s in shares]

    @staticmethod
    def get_overdue_for_cleanup():
        db = get_db()
        shares = db.execute(
            "SELECT * FROM shares WHERE status IN ('expired', 'revoked', 'limit_reached')"
        ).fetchall()
        db.close()
        return [dict(s) for s in shares]

    @staticmethod
    def update_status(share_id, status):
        db = get_db()
        db.execute(
            "UPDATE shares SET status = ? WHERE id = ?", (status, share_id)
        )
        db.commit()
        db.close()

    @staticmethod
    def is_valid(share):
        if not share:
            return False
        if share["revoked"]:
            return False
        if share["status"] in ("expired", "revoked", "limit_reached", "deleted"):
            return False
        now = datetime.now(timezone.utc).isoformat()
        if share["expires_at"] < now:
            return False
        if share["download_count"] >= share["max_downloads"]:
            return False
        return True


class AuditLog:
    @staticmethod
    def log(share_id, action, details=None, ip_address=None):
        db = get_db()
        db.execute(
            "INSERT INTO audit_log (share_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
            (share_id, action, details, ip_address),
        )
        db.commit()
        db.close()
