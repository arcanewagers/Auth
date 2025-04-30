from sqlalchemy import text  
from src.database.base import(
    Base, 
    engine, 
    SessionLocal, 
    get_db, 
    init_db_extensions
)
import logging


logger = logging.getLogger(__name__)

def init_database():
    """Initialize complete database setup"""
    try:
        init_db_extensions()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def test_database_connection():
    """Test database connection and log status"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# Export commonly used components
__all__ = [
    'Base',
    'engine',
    'SessionLocal',
    'get_db',
    'init_database',
    'test_database_connection'
]