import os
import logging
import random
from sqlalchemy.orm import Session
from app.crud.alert import get_alert_rules, create_alert
from app.schemas.alert import AlertCreate
from app.models.alert import NotificationLog
from app.services.whatsapp import whatsapp_client

logger = logging.getLogger(__name__)

WHATSAPP_TO_NUMBER = os.getenv("WHATSAPP_TO_NUMBER")

def send_whatsapp_notification(db: Session, alert_id: int, message: str):
    logger.info(f"Sending WhatsApp notification for alert {alert_id}")
    
    # Store pending state
    log = NotificationLog(alert_id=alert_id, message=message, status="PENDING")
    db.add(log)
    db.commit()
    db.refresh(log)
    
    if not WHATSAPP_TO_NUMBER:
        log.status = "FAILED"
        log.error_reason = "WHATSAPP_TO_NUMBER not configured"
        db.commit()
        return

    success, error = whatsapp_client.send_text_message(WHATSAPP_TO_NUMBER, message)
    
    if success:
        log.status = "SENT"
    else:
        log.status = "FAILED"
        log.error_reason = error
        
    db.commit()

def generate_report(db: Session, report_type: str):
    # Mock report generation
    if report_type == "daily_report":
        message = "Daily Report: Sales: $4500, Pending Credit: $1200, Low Stock Items: 5."
    elif report_type == "weekly_report":
        message = "Weekly Report: Sales: $32000, Best Seller: Item A, Critical Low Stock: 12."
    else:
        message = f"{report_type} generated."
        
    logger.info(f"Report generated: {message}")
    send_whatsapp_notification(db, None, message)

def evaluate_rules(db: Session):
    logger.info("Evaluating alert rules...")
    rules = get_alert_rules(db)
    
    # Mock data for demonstration purposes
    mock_data = {
        'quantity': random.uniform(5, 50),
        'expiry_days': random.uniform(1, 30),
        'pending_credit': random.uniform(0, 10000),
        'sales_target': random.uniform(100, 5000)
    }

    for rule in rules:
        if not rule.is_active:
            continue
            
        triggered = False
        message = ""
        
        # Check based on rule type
        if rule.type == 'quantity':
            current_val = mock_data['quantity']
            if rule.condition == '<' and current_val < rule.threshold:
                triggered = True
                message = f"Quantity Alert: {rule.name} (Current: {current_val:.1f} < Threshold: {rule.threshold})"
        elif rule.type == 'expiry':
            current_val = mock_data['expiry_days']
            if rule.condition == '<' and current_val < rule.threshold:
                triggered = True
                message = f"Expiry Alert: {rule.name} (Expires in {current_val:.1f} days, Threshold: {rule.threshold})"
        elif rule.type == 'pending_credit':
            current_val = mock_data['pending_credit']
            if rule.condition == '>' and current_val > rule.threshold:
                triggered = True
                message = f"Credit Alert: {rule.name} (Pending: {current_val:.1f} > Threshold: {rule.threshold})"
        elif rule.type == 'sales_target':
            current_val = mock_data['sales_target']
            if rule.condition == '<' and current_val < rule.threshold:
                triggered = True
                message = f"Sales Alert: {rule.name} (Current: {current_val:.1f} < Target: {rule.threshold})"
        elif rule.type in ['daily_report', 'weekly_report']:
            generate_report(db, rule.type)
            continue
                
        if triggered:
            logger.info(f"Rule triggered: {message}")
            alert = create_alert(db, AlertCreate(rule_id=rule.id, message=message))
            send_whatsapp_notification(db, alert.id, message)
