import os
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class TelegramAPIError(Exception):
    pass

class TelegramClient:
    def __init__(self):
        if TELEGRAM_BOT_TOKEN:
            self.url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        else:
            self.url = ""
        self.headers = {
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, TelegramAPIError))
    )
    def _send_request(self, payload: dict):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials missing. Skipping message send.")
            return

        with httpx.Client() as client:
            response = client.post(self.url, headers=self.headers, json=payload, timeout=10.0)
            
            if response.status_code >= 500:
                raise TelegramAPIError(f"Server error from Telegram: {response.status_code}")
            
            response.raise_for_status()
            return response.json()

    def send_telegram_alert(self, message: str):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        try:
            self._send_request(payload)
            logger.info(f"Successfully sent Telegram message to chat {TELEGRAM_CHAT_ID}")
            return True, None
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

telegram_client = TelegramClient()
