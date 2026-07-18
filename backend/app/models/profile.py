from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)
    telegram_chat_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
