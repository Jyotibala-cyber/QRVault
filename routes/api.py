import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file, current_app
from database.models import Share, AuditLog
from security.tokens import hash_token
from security.rate_limit import rate_limit_download, rate_limit_share
from services.file_service import get_encrypted_file_path, delete_encrypted_file
from security.validation import safe_path

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


@api_bp.route("/share/<token>/status")
@rate_limit_share
def share_status(token):
    token_h = hash_token(token)
    share = Share.find_by_token_hash(token_h)
    if not share:
        return jsonify({"error": "Share not found"}), 404

    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(share["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = max(0, int((expires_at - now).total_seconds()))

    return jsonify({
        "filename": share["original_filename"],
        "file_size": share["file_size"],
        "mime_type": share["mime_type"],
        "status": share["status"],
        "expires_at": share["expires_at"],
        "remaining_seconds": remaining,
        "download_count": share["download_count"],
        "max_downloads": share["max_downloads"],
        "revoked": bool(share["revoked"]),
        "has_password": bool(share.get("password_hash")),
    })


@api_bp.route("/share/<token>/authorize", methods=["POST"])
@rate_limit_share
def authorize_download(token):
    token_h = hash_token(token)
    share = Share.find_by_token_hash(token_h)

    if not share:
        return jsonify({"error": "Share not found"}), 404

    if not Share.is_valid(share):
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(share["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if share["revoked"] or share["status"] == "revoked":
            return jsonify({"error": "Access has been revoked"}), 403
        if expires_at < now or share["status"] == "expired":
            return jsonify({"error": "Link has expired"}), 410
        if share["download_count"] >= share["max_downloads"]:
            return jsonify({"error": "Download limit reached"}), 403
        return jsonify({"error": "Share is no longer valid"}), 403

    data = request.get_json(silent=True) or {}
    password = data.get("password")

    if share.get("password_hash"):
        if not password:
            return jsonify({"error": "Password required", "password_required": True}), 401
        import hashlib
        password_h = hashlib.sha256(password.encode()).hexdigest()
        if password_h != share["password_hash"]:
            AuditLog.log(share["id"], "download_rejected", "Wrong password", request.remote_addr)
            return jsonify({"error": "Invalid password"}), 401

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    AuditLog.log(share["id"], "download_authorized", f"IP: {client_ip}", client_ip)

    return jsonify({
        "authorized": True,
        "filename": share["original_filename"],
        "file_size": share["file_size"],
        "mime_type": share["mime_type"],
    })


@api_bp.route("/share/<token>/download")
@rate_limit_download
def download_file(token):
    token_h = hash_token(token)
    share = Share.find_by_token_hash(token_h)

    if not share:
        return jsonify({"error": "Share not found"}), 404

    if not Share.is_valid(share):
        return jsonify({"error": "Share is no longer valid"}), 403

    safe = safe_path(current_app.config.get("STORAGE_PATH", "storage/encrypted"), share["stored_filename"])
    if not safe or not safe.exists():
        return jsonify({"error": "File not found"}), 404

    with open(str(safe), "rb") as f:
        file_data = f.read()

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    updated_share = Share.increment_download(share["id"])
    AuditLog.log(share["id"], "download_completed", f"IP: {client_ip}", client_ip)

    if updated_share and updated_share["download_count"] >= updated_share["max_downloads"]:
        Share.update_status(share["id"], "limit_reached")
        AuditLog.log(share["id"], "limit_reached", "Max downloads hit")
        delete_encrypted_file(share["stored_filename"])
        AuditLog.log(share["id"], "file_auto_deleted", "Limit reached")

    response = current_app.response_class(
        response=file_data,
        status=200,
        mimetype="application/octet-stream",
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Content-Type"] = "application/octet-stream"
    return response


@api_bp.route("/manage/<management_token>/revoke", methods=["POST"])
def revoke_share(management_token):
    mgmt_h = hash_token(management_token)
    share = Share.find_by_management_token(mgmt_h)
    if not share:
        return jsonify({"error": "Invalid management token"}), 404

    Share.revoke(share["id"])
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    AuditLog.log(share["id"], "share_revoked", f"IP: {client_ip}", client_ip)

    return jsonify({"success": True, "message": "Share revoked successfully"})


@api_bp.route("/manage/<management_token>", methods=["DELETE"])
def delete_share(management_token):
    mgmt_h = hash_token(management_token)
    share = Share.find_by_management_token(mgmt_h)
    if not share:
        return jsonify({"error": "Invalid management token"}), 404

    delete_encrypted_file(share["stored_filename"])
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    AuditLog.log(share["id"], "share_deleted", f"IP: {client_ip}", client_ip)
    Share.delete(share["id"])

    return jsonify({"success": True, "message": "Share deleted successfully"})


@api_bp.route("/manage/<management_token>/status")
def manage_status(management_token):
    mgmt_h = hash_token(management_token)
    share = Share.find_by_management_token(mgmt_h)
    if not share:
        return jsonify({"error": "Invalid management token"}), 404

    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(share["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = max(0, int((expires_at - now).total_seconds()))

    return jsonify({
        "filename": share["original_filename"],
        "file_size": share["file_size"],
        "mime_type": share["mime_type"],
        "status": share["status"],
        "expires_at": share["expires_at"],
        "remaining_seconds": remaining,
        "download_count": share["download_count"],
        "max_downloads": share["max_downloads"],
        "revoked": bool(share["revoked"]),
    })
