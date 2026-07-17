import os
import json
import logging
import urllib.request
import urllib.error
import time
import functools
from sqlalchemy import inspect, text
from app.core.database import engine as db_engine
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    pass

class LLMEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def _send_request_with_retry(self, req) -> dict:
        max_retries = 5
        delay = 1.0
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req) as res:
                    return json.loads(res.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code in (429, 503) and attempt < max_retries - 1:
                    logger.warning(f"Gemini API rate limited/busy ({e.code}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                elif e.code == 429:
                    raise RateLimitExceeded("The AI service is temporarily busy. Please try again in a few moments.")
                else:
                    raise e

    def validate_api_key(self):
        logger.info("LLMEngine: Validating Gemini API Key and model accessibility...")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
        
        # Lightweight check: retrieve metadata for the configured model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash?key={self.api_key}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                if "name" in response_data and "models/gemini-2.5-flash" in response_data["name"]:
                    logger.info("LLMEngine: Gemini key and models/gemini-2.5-flash model verified successfully.")
                    return True
                else:
                    raise ValueError(f"Gemini API returned unexpected response: {response_data}")
        except Exception as e:
            logger.error(f"LLMEngine validation failed: {e}")
            raise ConnectionError(f"Failed to authenticate with Gemini or access models/gemini-2.5-flash: {e}")

    def get_db_state(self) -> dict:
        state = {}
        try:
            inspector = inspect(db_engine)
            for table_name in inspector.get_table_names():
                with db_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT * FROM {table_name}"))
                    state[table_name] = [dict(row) for row in result.mappings()]
        except Exception as e:
            logger.error(f"Error fetching DB state: {e}")
        return state

    @functools.lru_cache(maxsize=100)
    def _cached_generate_action_plan(self, text_input: str, db_state_json: str) -> str:
        # Caches the raw response text based on the text_input and the JSON representation of the DB state
        schema_def = {
            "language": "detected language",
            "intent": "user intent description",
            "confirmation_required": False,
            "operations": [
                {
                    "type": "create_table | insert | update | delete | select | alter_table | set_limit",
                    "target": "table_name",
                    "data": {},
                    "conditions": {},
                    "columns": [],
                    "meta": {}
                }
            ],
            "response": "draft friendly response in user's same language and script"
        }
        schema_json = json.dumps(schema_def, indent=2)

        prompt = f"""
You are the database planning engine for a shop inventory app named "Vita".
Your job is to analyze the user's intent and output a JSON object containing:
1. "language": Detect the language and script of the user's input (e.g. English, Hinglish, Telugu).
2. "intent": A brief description of what the user wants to do.
3. "operations": A list of database operations to modify the database.
4. "response": A draft friendly response in the user's same language and script.

Small businesses use this to track imports (adding items/stock) and sales (sold items, which decreases stock).

The main table to use is "inventory", which must have these columns:
- id: integer (primary key)
- item_name: string (unique name of the product, e.g., "Bananas", "Apples")
- quantity: integer (current count in stock)
- status: string (either "In Stock" if quantity > 0 else "Out of Stock")
- alert_limit: integer (optional, threshold for low stock alert. Update this if user sets/removes a limit)

Here is the current state of the database:
{db_state_json}

User request: "{text_input}"

Decide whether to CREATE the "inventory" table first if it does not exist in the current state.
If adding/importing items:
- If the item exists in "inventory", update quantity by adding new quantity.
- If it does not exist, insert a new record.
If recording sales or removing items:
- First check the available quantity of the item in the current state.
- You MUST output an "update" operation and include a "meta" object with "requested_deduction" set to the exact amount the user wants to remove. 
- Do not clamp the quantity to 0. Calculate the new quantity by subtracting the requested amount from the current quantity, even if it results in a negative number (the backend will perform strict validation).
- If the item does not exist, explain in response that item was not found.
If the user asks to set, update, or remove an alert limit / threshold for a product (e.g. "set limit 5 for eggs", "alert me when rice is below 10"):
- Output a "set_limit" operation for "inventory".
- Set "conditions" to match the item name (e.g. {"item_name": "Eggs"}).
- Set "alert_limit" in "data" to the requested number. To remove a limit, set it to null.
- Draft response: "Alert limit for <Item Name> has been set to <Limit>." (e.g., "Alert limit for Eggs has been set to 5.")
If deleting/removing specific items (e.g. "remove eggs"):
- Output a "delete" operation with "conditions" containing the item_name (e.g. {{"item_name": "Eggs"}}).
- After successful delete respond exactly: "<Item Name> removed from inventory." (e.g., "Eggs removed from inventory.")
If the user asks to clear all, delete everything, or remove all items:
- Set "confirmation_required": true instead of generating SQL/operations.
If the user explicitly confirms clearing the entire inventory (e.g. "confirm delete all", "yes clear everything"):
- Output a "delete_all" operation with target "inventory" and set "confirmation_required": false.
If the user asks to see, show, list, or display inventory, or searches for a product by name (e.g., "show inventory", "search for milk", "do I have eggs", "show out-of-stock items", "find rice"):
- Output a "select" operation for "inventory".
- If searching by name, add "item_name" to "conditions" (e.g. {"item_name": "Milk"}). The backend will handle partial matching.
- Do not output "select" for normal conversational responses unless they explicitly ask to see inventory/products.

Multilingual Rules:
- Let Gemini detect the input language.
- Always respond in the same language and script as the user's input.
- Preserve mixed-language conversations (e.g., Hinglish, Telugu-English) exactly in the response.
- Never translate unless explicitly requested.

Generate the action plan. Output format must be EXACTLY:
{schema_json}

Only return valid JSON. Do not write any explanations or markdown formatting outside the JSON.
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        response_data = self._send_request_with_retry(req)
        return response_data["candidates"][0]["content"]["parts"][0]["text"]

    def generate_action_plan(self, text_input: str) -> dict:
        logger.info(f"LLMEngine: Processing prompt: {text_input}")
        db_state = self.get_db_state()
        db_state_json = json.dumps(db_state, indent=2)
        response_text = self._cached_generate_action_plan(text_input, db_state_json)
        return json.loads(response_text)


    def generate_multimodal_plan(self, text_prompt: str, image_bytes: bytes, mime_type: str) -> dict:
        import base64
        logger.info("LLMEngine: Processing multimodal prompt...")
        db_state = self.get_db_state()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        schema_def = {
            "language": "detected language",
            "intent": "user intent description",
            "confirmation_required": False,
            "operations": [
                {
                    "type": "create_table | insert | update | delete | select | alter_table | set_limit",
                    "target": "table_name",
                    "data": {},
                    "conditions": {},
                    "columns": [],
                    "meta": {}
                }
            ],
            "response": "draft friendly response in user's same language and script"
        }
        schema_json = json.dumps(schema_def, indent=2)

        prompt = f"""
You are the database planning engine for a shop inventory app named "Vita".
Your job is to analyze the uploaded image and output a JSON object containing:
1. "language": Detect the language and script of the user's input/context (e.g. English, Hinglish, Telugu, Spanish, Telugu-English mixed, etc.).
2. "intent": A brief description of what the user wants to do.
3. "operations": A list of database operations to modify the database.
4. "response": A draft friendly response in the user's same language and script.

The main table to use is "inventory", which must have these columns:
- id: integer (primary key)
- item_name: string (unique name of the product, e.g., "Bananas", "Apples")
- quantity: integer (current count in stock)
- status: string (either "In Stock" if quantity > 0 else "Out of Stock")
- alert_limit: integer (optional, threshold for low stock alert. Update this if user sets/removes a limit)

Here is the current state of the database:
{json.dumps(db_state, indent=2)}

User instruction: "{text_prompt}"

Identify product names and quantities visible in the image.
If item exists, update quantity (adding imports, subtracting sales).
- First check the available quantity of the item in the current state when recording sales.
- You MUST output an "update" operation and include a "meta" object with "requested_deduction" set to the exact amount the user wants to remove.
- Do not clamp the quantity to 0. Calculate the new quantity by subtracting the requested amount from the current quantity, even if it results in a negative number (the backend will perform strict validation).
If item does not exist, insert it. Ensure table "inventory" is created if it does not exist.
If the user asks to set, update, or remove an alert limit / threshold for a product (e.g. "set limit 5 for eggs", "alert me when rice is below 10"):
- Output a "set_limit" operation targeting the item in "conditions".
- Set "alert_limit" in "data" to the requested number, or null to remove it.
- Draft response: "Alert limit for <Item Name> has been set to <Limit>."
If deleting/removing specific items (e.g. "remove eggs"):
- Output a "delete" operation with "conditions" containing the item_name (e.g. {{"item_name": "Eggs"}}).
- After successful delete respond exactly: "<Item Name> removed from inventory." (e.g., "Eggs removed from inventory.")
If the user asks to clear all, delete everything, or remove all items:
- Set "confirmation_required": true instead of generating SQL/operations.
If the user explicitly confirms clearing the entire inventory (e.g. "confirm delete all", "yes clear everything"):
- Output a "delete_all" operation with target "inventory" and set "confirmation_required": false.
If the user asks to see, show, list, or display inventory, or searches for a product by name (e.g., "show inventory", "search for milk", "do I have eggs", "show out-of-stock items", "find rice"):
- Output a "select" operation for "inventory".
- If searching by name, add "item_name" to "conditions" (e.g. {"item_name": "Milk"}). The backend will handle partial matching.
- Do not output "select" for normal conversational responses unless they explicitly ask to see inventory/products.

Multilingual Rules:
- Let Gemini detect the input language.
- Always respond in the same language and script as the user's input.
- Preserve mixed-language conversations (e.g., Hinglish, Telugu-English) exactly in the response.
- Never translate unless explicitly requested.

Generate the action plan. Output format must be EXACTLY:
{schema_json}

Only return valid JSON. Do not write any explanations or markdown formatting outside the JSON.
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64_image
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        # Do NOT catch exception silently. Let it bubble up to the pipeline stage.
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        response_data = self._send_request_with_retry(req)
        response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(response_text)



llm_engine = LLMEngine()
