import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify
from database.models import Share, AuditLog
from security.tokens import hash_token
from services.file_service import delete_encrypted_file

logger = logging.getLogger(__name__)
sharing_bp = Blueprint("sharing", __name__)


def _delete_file_if_terminal(share):
    """Delete file immediately when share reaches terminal state."""
    if share["status"] in ("expired", "revoked", "limit_reached"):
        deleted = delete_encrypted_file(share["stored_filename"])
        if deleted:
            AuditLog.log(share["id"], "file_auto_deleted", f"State: {share['status']}")
            logger.info(f"Auto-deleted file for share {share['id']} (state: {share['status']})")


def _get_share_or_error(token):
    token_h = hash_token(token)
    share = Share.find_by_token_hash(token_h)
    if not share:
        return None, "not_found"
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(share["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now and share["status"] != "expired":
        Share.update_status(share["id"], "expired")
        share["status"] = "expired"
        _delete_file_if_terminal(share)
    if share["revoked"] and share["status"] != "revoked":
        Share.update_status(share["id"], "revoked")
        share["status"] = "revoked"
        _delete_file_if_terminal(share)
    if share["download_count"] >= share["max_downloads"] and share["status"] not in ("limit_reached", "expired", "revoked"):
        Share.update_status(share["id"], "limit_reached")
        share["status"] = "limit_reached"
        _delete_file_if_terminal(share)
    return share, share["status"]


@sharing_bp.route("/share/<token>")
def share_page(token):
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    share, status = _get_share_or_error(token)

    if not share:
        AuditLog.log(None, "share_access_failed", f"Token not found", client_ip)
        return render_template("error.html", error_type="not_found"), 404

    AuditLog.log(share["id"], "share_accessed", f"IP: {client_ip}", client_ip)

    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(share["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = max(0, int((expires_at - now).total_seconds()))

    has_password = bool(share.get("password_hash"))

    if status == "expired":
        return render_template("error.html", error_type="expired"), 410
    elif status == "revoked":
        return render_template("error.html", error_type="revoked"), 403
    elif status == "limit_reached":
        return render_template("error.html", error_type="limit_reached"), 403

    return render_template(
        "share.html",
        share=share,
        token=token,
        remaining_seconds=remaining,
        has_password=has_password,
    )


@sharing_bp.route("/manage/<management_token>")
def manage_page(management_token):
    mgmt_h = hash_token(management_token)
    share = Share.find_by_management_token(mgmt_h)
    if not share:
        return render_template("error.html", error_type="not_found"), 404

    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(share["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = max(0, int((expires_at - now).total_seconds()))
    is_expired = expires_at < now

    return render_template(
        "manage.html",
        share=share,
        management_token=management_token,
        remaining_seconds=remaining,
        is_expired=is_expired,
    )
