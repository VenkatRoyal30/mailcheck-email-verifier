import pytest
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import TestingConfig
from app.database import Base, get_engine, init_engine

@pytest.fixture(scope="session")
def app():
    """Create test application instance configured with in-memory SQLite."""
    test_app = create_app(TestingConfig)
    return test_app

@pytest.fixture(scope="function")
def client(app):
    """Test client for API testing."""
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_db(app):
    """Ensure database tables are cleaned before each test."""
    with app.app_context():
        engine = get_engine()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield
