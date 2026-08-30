import os
from pathlib import Path

BLOCKED_EXTENSIONS = {
    "exe", "bat", "cmd", "com", "msi", "scr", "pif",
    "vbs", "vbe", "js", "jse", "ws", "wsh", "wsc",
    "hta", "cpl", "inf", "reg", "rgs", "sct", "shb",
    "shs", "lnk", "url", "application", "gadget",
}


def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal and injection."""
    if not filename:
        return "unnamed_file"
    filename = os.path.basename(filename)
    filename = filename.replace("..", "_")
    filename = filename.replace("/", "_").replace("\\", "_")
    filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    filename = filename.strip(". ")
    if not filename:
        filename = "unnamed_file"
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename


def validate_file_extension(filename):
    """Check if file extension is allowed."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in BLOCKED_EXTENSIONS:
        return False, f"File type .{ext} is not allowed"
    return True, None


def validate_file_size(size, max_size):
    """Validate file size against limit."""
    if size <= 0:
        return False, "File is empty"
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File exceeds maximum size of {max_mb:.0f}MB"
    return True, None


def validate_expiry(expiry_minutes):
    """Validate expiry time."""
    valid_options = [5, 10, 30, 60, 120, 240, 480, 1440]
    try:
        expiry = int(expiry_minutes)
    except (TypeError, ValueError):
        return False, "Invalid expiry time"
    if expiry not in valid_options:
        return False, "Invalid expiry option"
    return True, expiry


def validate_max_downloads(max_downloads):
    """Validate max downloads setting."""
    valid_options = [1, 3, 5, 10, 25, 50]
    try:
        downloads = int(max_downloads)
    except (TypeError, ValueError):
        return False, "Invalid download limit"
    if downloads not in valid_options:
        return False, "Invalid download limit option"
    return True, downloads


def safe_path(base_dir, filename):
    """Ensure a path is within the base directory."""
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)):
        return None
    return target
