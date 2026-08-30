import os
import json
import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from database.models import Share, AuditLog
from security.tokens import (
    generate_share_token,
    generate_management_token,
    hash_token,
    generate_file_id,
)
from security.validation import (
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    validate_expiry,
    validate_max_downloads,
)
from security.rate_limit import rate_limit_upload
from services.file_service import save_encrypted_file, compute_file_hash
from services.qr_service import generate_qr_code

logger = logging.getLogger(__name__)
upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/api/upload", methods=["POST"])
@rate_limit_upload
def upload_file():
    if "encrypted_file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["encrypted_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    original_filename = file.filename
    valid_ext, ext_error = validate_file_extension(original_filename)
    if not valid_ext:
        return jsonify({"error": ext_error}), 400

    sanitized_name = sanitize_filename(original_filename)

    file_data = file.read()
    max_size = current_app.config.get("MAX_FILE_SIZE", 50 * 1024 * 1024)
    valid_size, size_error = validate_file_size(len(file_data), max_size)
    if not valid_size:
        return jsonify({"error": size_error}), 400

    expiry_raw = request.form.get("expiry", "10")
    valid_expiry, expiry_result = validate_expiry(expiry_raw)
    if not valid_expiry:
        return jsonify({"error": expiry_result}), 400
    expiry_minutes = expiry_result

    downloads_raw = request.form.get("max_downloads", "3")
    valid_downloads, downloads_result = validate_max_downloads(downloads_raw)
    if not valid_downloads:
        return jsonify({"error": downloads_result}), 400
    max_downloads = downloads_result

    password_hash = request.form.get("password_hash")
    if password_hash:
        password_hash = password_hash[:256]

    file_id = generate_file_id()
    stored_filename = f"{file_id}.enc"

    save_encrypted_file(file_data, stored_filename)

    share_token = generate_share_token()
    mgmt_token = generate_management_token()
    token_h = hash_token(share_token)
    mgmt_h = hash_token(mgmt_token)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expiry_minutes)
    expires_at_str = expires_at.isoformat()

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    share_id = Share.create(
        token_hash=token_h,
        management_token_hash=mgmt_h,
        original_filename=sanitized_name,
        stored_filename=stored_filename,
        file_size=len(file_data),
        mime_type=file.content_type or "application/octet-stream",
        expires_at=expires_at_str,
        max_downloads=max_downloads,
        password_hash=password_hash,
        created_ip=client_ip,
    )

    AuditLog.log(share_id, "share_created", f"File: {sanitized_name}", client_ip)

    file_hash = compute_file_hash(file_data)

    base_url = request.host_url.rstrip("/")
    share_url = f"{base_url}/share/{share_token}"
    qr_url = f"{share_url}#key"

    qr_image = generate_qr_code(share_url)

    logger.info(f"Share created: {share_id}, file: {sanitized_name}")

    return jsonify({
        "success": True,
        "share_id": share_id,
        "share_token": share_token,
        "management_token": mgmt_token,
        "share_url": share_url,
        "qr_code": qr_image,
        "expires_at": expires_at_str,
        "max_downloads": max_downloads,
        "filename": sanitized_name,
        "file_size": len(file_data),
        "file_hash": file_hash,
    })
