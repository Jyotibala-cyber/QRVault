import time
from functools import wraps
from flask import request, jsonify, g

_rate_limit_store = {}


def _get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "unknown"


def _cleanup_old_entries(key_prefix, window):
    now = time.time()
    to_delete = []
    for key, entries in _rate_limit_store.items():
        if key.startswith(key_prefix):
            _rate_limit_store[key] = [e for e in entries if e > now - window]
            if not _rate_limit_store[key]:
                to_delete.append(key)
    for key in to_delete:
        del _rate_limit_store[key]


def rate_limit(max_requests, window_seconds, key_prefix="default"):
    """Simple in-memory rate limiter."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = _get_client_ip()
            key = f"{key_prefix}:{client_ip}"
            now = time.time()

            if key not in _rate_limit_store:
                _rate_limit_store[key] = []

            _rate_limit_store[key] = [
                t for t in _rate_limit_store[key] if t > now - window_seconds
            ]

            if len(_rate_limit_store[key]) >= max_requests:
                retry_after = int(window_seconds - (now - _rate_limit_store[key][0]))
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                }), 429

            _rate_limit_store[key].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit_upload(f):
    """Rate limit for uploads: 30 per hour."""
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = _get_client_ip()
        key = f"upload:{client_ip}"
        now = time.time()
        window = 3600

        if key not in _rate_limit_store:
            _rate_limit_store[key] = []
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > now - window]

        if len(_rate_limit_store[key]) >= 30:
            return jsonify({"error": "Upload rate limit exceeded. Try again later."}), 429
        _rate_limit_store[key].append(now)
        return f(*args, **kwargs)
    return decorated


def rate_limit_download(f):
    """Rate limit for downloads: 60 per hour."""
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = _get_client_ip()
        key = f"download:{client_ip}"
        now = time.time()
        window = 3600

        if key not in _rate_limit_store:
            _rate_limit_store[key] = []
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > now - window]

        if len(_rate_limit_store[key]) >= 60:
            return jsonify({"error": "Download rate limit exceeded."}), 429
        _rate_limit_store[key].append(now)
        return f(*args, **kwargs)
    return decorated


def rate_limit_share(f):
    """Rate limit for share access: 100 per hour."""
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = _get_client_ip()
        key = f"share:{client_ip}"
        now = time.time()
        window = 3600

        if key not in _rate_limit_store:
            _rate_limit_store[key] = []
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > now - window]

        if len(_rate_limit_store[key]) >= 100:
            return jsonify({"error": "Too many requests."}), 429
        _rate_limit_store[key].append(now)
        return f(*args, **kwargs)
    return decorated
