from sqlalchemy.orm import Session
from app.models.alert import AlertRule, Alert
from app.schemas.alert import AlertRuleCreate, AlertCreate

def get_alert_rule(db: Session, rule_id: int):
    return db.query(AlertRule).filter(AlertRule.id == rule_id).first()

def get_alert_rules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AlertRule).offset(skip).limit(limit).all()

def create_alert_rule(db: Session, rule: AlertRuleCreate):
    db_rule = AlertRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def get_alerts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

def create_alert(db: Session, alert: AlertCreate):
    db_alert = Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert
