import os
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

class WhatsAppAPIError(Exception):
    pass

class WhatsAppClient:
    def __init__(self):
        self.url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, WhatsAppAPIError))
    )
    def _send_request(self, payload: dict):
        if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp credentials missing. Skipping message send.")
            return

        with httpx.Client() as client:
            response = client.post(self.url, headers=self.headers, json=payload, timeout=10.0)
            
            if response.status_code >= 500:
                raise WhatsAppAPIError(f"Server error from Meta: {response.status_code}")
            
            response.raise_for_status()
            return response.json()

    def send_text_message(self, to_number: str, message: str):
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        try:
            self._send_request(payload)
            logger.info(f"Successfully sent WhatsApp message to {to_number}")
            return True, None
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

whatsapp_client = WhatsAppClient()
