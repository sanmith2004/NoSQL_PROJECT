from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from config import Config
from routes.events import events_bp
from routes.registrations import reg_bp
from routes.admin import admin_bp
from routes.notifications import notif_bp

def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(events_bp)
    app.register_blueprint(reg_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notif_bp)

    # Serve frontend static files
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/admin-panel")
    def admin_panel():
        return send_from_directory(frontend_dir, "admin.html")

    @app.route("/event/<event_id>")
    def event_detail(event_id):
        return send_from_directory(frontend_dir, "event_detail.html")

    @app.route("/static/<path:filename>")
    def static_files(filename):
        static_dir = os.path.join(frontend_dir, "static")
        return send_from_directory(static_dir, filename)

    @app.route("/health")
    def health():
        from services.redis_service import get_redis
        from database import get_db
        redis_ok = get_redis() is not None
        try:
            get_db().command("ping")
            mongo_ok = True
        except Exception:
            mongo_ok = False
        return {"status": "ok", "redis": redis_ok, "mongodb": mongo_ok}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000, threaded=True)
