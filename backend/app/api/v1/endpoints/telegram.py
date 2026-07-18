from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.profile import Profile
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook to receive messages from Telegram bot.
    Expects updates containing user contact info or text messages with phone number.
    """
    try:
        update = await request.json()
    except Exception:
        return {"status": "ok"}
        
    logger.info(f"Received Telegram update: {update}")
    
    if "message" in update:
        message = update["message"]
        chat_id = str(message.get("chat", {}).get("id"))
        
        # Scenario 1: User sends a contact explicitly via Telegram attachment
        if "contact" in message:
            phone_number = message["contact"].get("phone_number", "")
            if phone_number:
                # normalize phone number (e.g. remove +)
                if not phone_number.startswith("+"):
                    phone_number = "+" + phone_number
                    
                profile = db.query(Profile).filter(Profile.phone_number == phone_number).first()
                if profile:
                    profile.telegram_chat_id = chat_id
                    db.commit()
                    from app.services.telegram import telegram_client
                    telegram_client.send_telegram_alert("Your account is now linked!", chat_id)
                else:
                    from app.services.telegram import telegram_client
                    telegram_client.send_telegram_alert("Phone number not found in our records. Please update your profile in the app.", chat_id)
                    
        # Scenario 2: User types their phone number or /start
        elif "text" in message:
            text = message["text"].strip()
            if text.startswith("/start"):
                parts = text.split(" ")
                # user can do `/start +919999999999`
                if len(parts) > 1:
                    phone_number = parts[1]
                    if not phone_number.startswith("+"):
                        phone_number = "+" + phone_number
                    
                    profile = db.query(Profile).filter(Profile.phone_number == phone_number).first()
                    if profile:
                        profile.telegram_chat_id = chat_id
                        db.commit()
                        from app.services.telegram import telegram_client
                        telegram_client.send_telegram_alert("Your account is now linked!", chat_id)
                    else:
                        from app.services.telegram import telegram_client
                        telegram_client.send_telegram_alert("Phone number not found. Please sign up or update your profile first.", chat_id)
                else:
                    from app.services.telegram import telegram_client
                    telegram_client.send_telegram_alert("Welcome! Please reply with your phone number (e.g. +919999999999) or share your contact to link your account.", chat_id)
            else:
                # Just check if the text looks like a phone number
                if "+" in text or text.isdigit():
                    phone_number = text
                    if not phone_number.startswith("+"):
                        phone_number = "+" + phone_number
                        
                    profile = db.query(Profile).filter(Profile.phone_number == phone_number).first()
                    if profile:
                        profile.telegram_chat_id = chat_id
                        db.commit()
                        from app.services.telegram import telegram_client
                        telegram_client.send_telegram_alert("Your account is now linked successfully!", chat_id)

    return {"status": "ok"}
