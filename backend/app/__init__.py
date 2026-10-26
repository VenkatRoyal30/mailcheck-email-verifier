import logging
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from .database import init_engine, init_db
from .routes.health import health_bp
from .routes.verify import verify_bp
from .routes.history import history_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(config_class=None):
    """Application factory for MailCheck backend."""
    workspace_dir = Path(__file__).resolve().parent.parent.parent
    dist_dir = workspace_dir / "frontend" / "dist"

    app = Flask(
        __name__,
        static_folder=str(dist_dir) if dist_dir.exists() else None,
        static_url_path=""
    )

    if config_class is None:
        from config import Config
        config_class = Config

    app.config.from_object(config_class)

    # Initialize database engine and schema
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    init_engine(db_uri)
    with app.app_context():
        init_db()

    # Configure CORS
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    if cors_origins == "*":
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        allowed_list = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        CORS(app, resources={r"/api/*": {"origins": allowed_list}})

    # Register blueprints with /api prefix
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(verify_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")

    # Serve React SPA index
    @app.route("/", methods=["GET"])
    def serve_index():
        index_file = dist_dir / "index.html"
        if index_file.is_file():
            return send_from_directory(str(dist_dir), "index.html")
        return jsonify({
            "error": "Frontend build not found",
            "message": "Please run 'npm run build' inside the frontend directory."
        }), 404

    # Serve React SPA client routes, static assets, and ensure unknown API routes return 404 JSON
    @app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    def serve_spa(path):
        # 1. Any unhandled route under /api/* must return JSON 404
        if path.startswith("api/") or path == "api":
            return jsonify({"error": "Resource not found"}), 404

        # 2. Only GET and HEAD methods are valid for static assets and SPA pages
        if request.method not in ("GET", "HEAD"):
            return jsonify({"error": "Method not allowed on this endpoint"}), 405

        # 3. Check if the static file exists directly in dist_dir (assets, icons, etc.)
        target = dist_dir / path
        if target.is_file():
            return send_from_directory(str(dist_dir), path)

        # 4. For React client-side routes (e.g. /history, /verifier), serve index.html
        index_file = dist_dir / "index.html"
        if index_file.is_file():
            return send_from_directory(str(dist_dir), "index.html")

        return jsonify({"error": "Resource not found"}), 404

    # Safe error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "details": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api"):
            return jsonify({"error": "Resource not found"}), 404
        index_file = dist_dir / "index.html"
        if index_file.is_file():
            return send_from_directory(str(dist_dir), "index.html")
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed on this endpoint"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error. Please try again later."}), 500

    return app
