import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
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
    # Query real inventory stats from database
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    item_count = 0
    total_qty = 0
    low_stock_count = 0
    
    if "inventory" in tables:
        try:
            result = db.execute(text("SELECT item_name, quantity FROM inventory")).fetchall()
            item_count = len(result)
            for row in result:
                qty = row[1] or 0
                total_qty += qty
                if qty < 5:
                    low_stock_count += 1
        except Exception as e:
            logger.error(f"Error gathering stats for report: {e}")
            
    message = f"{report_type.replace('_', ' ').title()}: Total Unique Products: {item_count}, Total Units in Stock: {total_qty}, Low Stock Products (< 5 units): {low_stock_count}."
        
    logger.info(f"Real report generated: {message}")
    send_whatsapp_notification(db, None, message)

def evaluate_rules(db: Session):
    logger.info("Evaluating real alert rules against Supabase PostgreSQL...")
    rules = get_alert_rules(db)
    
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    for rule in rules:
        if not rule.is_active:
            continue
            
        # Handle report rules
        if rule.type in ['daily_report', 'weekly_report']:
            generate_report(db, rule.type)
            continue
            
        # Handle quantity rule
        if rule.type == 'quantity':
            if "inventory" not in tables:
                logger.warning("AlertManager: 'inventory' table does not exist. Skipping quantity check.")
                continue
                
            try:
                # Query all products that violate the threshold
                cond = rule.condition if rule.condition in ['<', '>', '=', '<=', '>='] else '<'
                query = text(f"SELECT item_name, quantity FROM inventory WHERE quantity {cond} :threshold")
                low_items = db.execute(query, {"threshold": rule.threshold}).fetchall()
                
                for item in low_items:
                    item_name = item[0]
                    qty = item[1]
                    message = f"Quantity Alert: {item_name} has triggered a low stock alert (Current: {qty} {cond} Threshold: {rule.threshold})"
                    
                    logger.info(f"Alert triggered: {message}")
                    alert = create_alert(db, AlertCreate(rule_id=rule.id, message=message))
                    send_whatsapp_notification(db, alert.id, message)
            except Exception as e:
                logger.error(f"Error evaluating quantity alert rule: {e}")
                
        # Expiry check
        elif rule.type == 'expiry':
            if "inventory" not in tables:
                continue
            cols = [c["name"] for c in inspector.get_columns("inventory")]
            if "expiry_days" in cols:
                try:
                    cond = rule.condition if rule.condition in ['<', '>', '=', '<=', '>='] else '<'
                    query = text(f"SELECT item_name, expiry_days FROM inventory WHERE expiry_days {cond} :threshold")
                    exp_items = db.execute(query, {"threshold": rule.threshold}).fetchall()
                    for item in exp_items:
                        item_name = item[0]
                        exp_days = item[1]
                        message = f"Expiry Alert: {item_name} expires in {exp_days} days (Threshold: {rule.threshold})"
                        logger.info(f"Alert triggered: {message}")
                        alert = create_alert(db, AlertCreate(rule_id=rule.id, message=message))
                        send_whatsapp_notification(db, alert.id, message)
                except Exception as e:
                    logger.error(f"Error evaluating expiry alert rule: {e}")
                    
        # Credit alert check
        elif rule.type == 'pending_credit':
            if "credits" not in tables:
                logger.warning("AlertManager: 'credits' table does not exist. Skipping pending credit check.")
                continue
            try:
                cond = rule.condition if rule.condition in ['<', '>', '=', '<=', '>='] else '>'
                query = text(f"SELECT customer_name, pending_amount FROM credits WHERE pending_amount {cond} :threshold")
                credit_items = db.execute(query, {"threshold": rule.threshold}).fetchall()
                for customer in credit_items:
                    cust_name = customer[0]
                    amount = customer[1]
                    message = f"Credit Alert: Customer {cust_name} pending amount is ${amount} (Threshold: {rule.threshold})"
                    logger.info(f"Alert triggered: {message}")
                    alert = create_alert(db, AlertCreate(rule_id=rule.id, message=message))
                    send_whatsapp_notification(db, alert.id, message)
            except Exception as e:
                logger.error(f"Error evaluating credit alert rule: {e}")
