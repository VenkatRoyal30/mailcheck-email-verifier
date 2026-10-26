from datetime import datetime, timezone
from flask import Blueprint, jsonify
from sqlalchemy import text
from ..database import get_engine

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def check_health():
    """Health check endpoint confirming API status and database connectivity."""
    db_status = "connected"
    try:
        engine = get_engine()
        if engine:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        else:
            db_status = "engine_not_initialized"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return jsonify({
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": "MailCheck SaaS API",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200
