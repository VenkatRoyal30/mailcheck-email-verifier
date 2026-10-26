import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionFactory = None

def init_engine(db_url: str):
    global _engine, _SessionFactory
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    _engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    _SessionFactory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=_engine))
    return _engine

def get_engine():
    return _engine

def get_session():
    if _SessionFactory is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _SessionFactory()

@contextmanager
def db_session():
    """Transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session rollback due to error: {e}")
        raise
    finally:
        session.close()

def init_db(engine=None):
    """Create all database tables based on registered models."""
    target_engine = engine or _engine
    if target_engine is None:
        raise RuntimeError("Engine must be initialized before init_db.")
    Base.metadata.create_all(bind=target_engine)
    logger.info("Database tables initialized successfully.")

