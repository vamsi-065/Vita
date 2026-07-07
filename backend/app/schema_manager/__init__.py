import logging
from sqlalchemy import MetaData
from app.core.database import engine

logger = logging.getLogger(__name__)

class SchemaManager:
    """
    Refreshes the database schema metadata caching.
    """
    def refresh(self):
        logger.info("SchemaManager: Refreshing database schema metadata...")
        # Force a refresh by reflecting the database again
        # This makes sure dynamic endpoints like /api/v1/tables see the new tables immediately
        metadata = MetaData()
        metadata.reflect(bind=engine)
        logger.info(f"Schema refresh complete. Found tables: {list(metadata.tables.keys())}")
        return True

schema_manager = SchemaManager()
