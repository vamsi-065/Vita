from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True) # e.g., 'quantity', 'expiry', 'pending_credit', 'sales_target'
    condition = Column(String) # '<', '>', '==', 'expires_in_days'
    threshold = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, index=True)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, index=True, nullable=True) # Optional, since reports might not map to a single alert
    message = Column(String)
    status = Column(String) # PENDING, SENT, FAILED
    error_reason = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
