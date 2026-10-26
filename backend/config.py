import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend or root directory if present
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "mailcheck-production-secret-key-change-me")
    
    # Database URL with fallback to local SQLite database in backend directory
    raw_db_url = os.environ.get("DATABASE_URL")
    if raw_db_url:
        # Normalize legacy postgres:// scheme to postgresql:// for SQLAlchemy compatibility
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        db_path = BASE_DIR / "mailcheck.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Verification pipeline limits & thresholds
    MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", "100"))
    DNS_TIMEOUT = float(os.environ.get("DNS_TIMEOUT", "3.0"))
    SMTP_TIMEOUT = float(os.environ.get("SMTP_TIMEOUT", "5.0"))
    SMTP_MAX_RETRIES = int(os.environ.get("SMTP_MAX_RETRIES", "1"))
    ENABLE_SMTP_BY_DEFAULT = os.environ.get("ENABLE_SMTP_BY_DEFAULT", "false").lower() in ("true", "1", "yes")
    
    # Retention policy in days for audit and storage
    RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))
    
    # CORS allowed origins
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    
    TESTING = False


class TestingConfig(Config):
    """Configuration for automated test execution."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DNS_TIMEOUT = 1.0
    SMTP_TIMEOUT = 1.0
    SMTP_MAX_RETRIES = 1
    MAX_BATCH_SIZE = 100

