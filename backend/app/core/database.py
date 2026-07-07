import os
import logging
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing or empty. PostgreSQL is required.")

# Normalize connection string for pg8000 driver
if DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
elif DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

logger.info(f"Connecting to Database host via pg8000 pooler...")
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseService:
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal

    def validate_connection(self):
        logger.info("DatabaseService: Validating PostgreSQL connection...")
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT 1;")).first()
            if not result or result[0] != 1:
                raise ConnectionError("Database health check query returned invalid response.")
        logger.info("DatabaseService: PostgreSQL connection successfully validated.")

    @contextmanager
    def transaction(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"DatabaseService Transaction failed, rolled back changes: {e}")
            raise e
        finally:
            session.close()

database_service = DatabaseService()
