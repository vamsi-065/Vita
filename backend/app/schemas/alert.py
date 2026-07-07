from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertRuleBase(BaseModel):
    name: str
    type: str
    condition: str
    threshold: float
    is_active: bool = True

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRule(AlertRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    rule_id: int
    message: str

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
