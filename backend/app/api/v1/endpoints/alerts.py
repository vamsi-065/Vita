from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.crud import alert as crud_alert
from app.schemas import alert as schema_alert

from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.post("/rules", response_model=schema_alert.AlertRule)
def create_alert_rule(rule: schema_alert.AlertRuleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return crud_alert.create_alert_rule(db=db, rule=rule, user_id=str(current_user.id))

@router.get("/rules", response_model=List[schema_alert.AlertRule])
def read_alert_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rules = crud_alert.get_alert_rules(db, skip=skip, limit=limit, user_id=str(current_user.id))
    return rules

@router.get("/", response_model=List[schema_alert.Alert])
def read_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    alerts = crud_alert.get_alerts(db, skip=skip, limit=limit, user_id=str(current_user.id))
    return alerts
