from routes.main import main_bp
from routes.upload import upload_bp
from routes.sharing import sharing_bp
from routes.api import api_bp


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(sharing_bp)
