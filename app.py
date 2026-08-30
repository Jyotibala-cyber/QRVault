import os
import logging
import threading
import time
from flask import Flask
from config import config_by_name
from database.db import init_db
from routes import register_routes
from security.headers import set_security_headers
from services.cleanup_service import run_cleanup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def start_cleanup_thread(app):
    def cleanup_loop():
        while True:
            time.sleep(app.config.get("CLEANUP_INTERVAL", 3600))
            try:
                with app.app_context():
                    run_cleanup()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    os.makedirs(app.config["STORAGE_PATH"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)

    init_db()
    register_routes(app)

    @app.after_request
    def after_request(response):
        return set_security_headers(response)

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error"}, 500

    @app.errorhandler(413)
    def too_large(e):
        return {"error": "File too large"}, 413

    start_cleanup_thread(app)
    logger.info("QRVault application started")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
