from flask import jsonify
from config.config import Config

def register_health_routes(app):
    @app.route("/health")
    def health():
        return jsonify(
            app=Config.APP_NAME,
            status="up",
            version=Config.APP_VERSION,
        )
