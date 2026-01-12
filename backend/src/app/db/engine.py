"""
Database engine and session management
SQLAlchemy 엔진 및 세션 관리
"""

from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session as SASession
from sqlalchemy.pool import QueuePool

from ..config import get_settings
from ..config.logger import get_logger

logger = get_logger()
settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    poolclass=QueuePool,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Event listener for connection pool
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set connection charset to utf8mb4"""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET NAMES utf8mb4")
    cursor.close()


def init_db() -> None:
    """
    Initialize database
    테이블 생성 (이미 존재하는 경우 스킵)
    """
    try:
        from .models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(
            "Failed to initialize database",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


def close_db() -> None:
    """
    Close database connections
    데이터베이스 연결 종료
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(
            "Error closing database connections",
            extra={"error": str(e)},
            exc_info=True
        )


@contextmanager
def get_db() -> Generator[SASession, None, None]:
    """
    Get database session (context manager)
    
    Yields:
        Session: SQLAlchemy session
    
    Example:
        ```python
        with get_db() as db:
            policy = db.query(Policy).first()
        ```
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(
            "Database session error",
            extra={"error": str(e)},
            exc_info=True
        )
        raise
    finally:
        db.close()


def get_db_session() -> SASession:
    """
    Get database session (for FastAPI dependency injection)
    
    Returns:
        Session: SQLAlchemy session
    
    Example:
        ```python
        @app.get("/policies")
        def get_policies(db: Session = Depends(get_db_session)):
            return db.query(Policy).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

