import os
from pathlib import Path

basedir = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    DATABASE_PATH = os.environ.get(
        "DATABASE_URL", str(basedir / "instance" / "qrvault.db")
    )
    STORAGE_PATH = os.environ.get(
        "STORAGE_PATH", str(basedir / "storage" / "encrypted")
    )
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
    RATE_LIMIT_DEFAULT = os.environ.get("RATE_LIMIT_DEFAULT", "200 per day")
    RATE_LIMIT_UPLOAD = os.environ.get("RATE_LIMIT_UPLOAD", "30 per hour")
    RATE_LIMIT_DOWNLOAD = os.environ.get("RATE_LIMIT_DOWNLOAD", "60 per hour")
    RATE_LIMIT_SHARE = os.environ.get("RATE_LIMIT_SHARE", "100 per hour")

    ALLOWED_EXTENSIONS = set()  # empty = allow all
    BLOCKED_EXTENSIONS = {
        "exe", "bat", "cmd", "com", "msi", "scr", "pif",
        "vbs", "vbe", "js", "jse", "ws", "wsh", "wsc",
        "hta", "cpl", "inf", "reg", "rgs", "sct", "shb",
        "shs", "lnk", "url", "application", "gadget",
    }

    CLEANUP_INTERVAL = 300  # 5 minutes
    RETENTION_PERIOD = 86400  # 24 hours after expiry


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    DATABASE_PATH = str(basedir / "instance" / "qrvault.db")
    STORAGE_PATH = str(basedir / "storage" / "encrypted")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
