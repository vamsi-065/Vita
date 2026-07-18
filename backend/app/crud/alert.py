from sqlalchemy.orm import Session
from app.models.alert import AlertRule, Alert
from app.schemas.alert import AlertRuleCreate, AlertCreate

def get_alert_rule(db: Session, rule_id: int, user_id: str):
    return db.query(AlertRule).filter(AlertRule.id == rule_id, AlertRule.user_id == user_id).first()

def get_alert_rules(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(AlertRule).filter(AlertRule.user_id == user_id).offset(skip).limit(limit).all()

def create_alert_rule(db: Session, rule: AlertRuleCreate, user_id: str):
    db_rule = AlertRule(**rule.dict(), user_id=user_id)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def get_alerts(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(Alert).filter(Alert.user_id == user_id).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

def create_alert(db: Session, alert: AlertCreate, user_id: str):
    db_alert = Alert(**alert.dict(), user_id=user_id)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert
