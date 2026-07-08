import os
import json
import logging
import urllib.request
import urllib.error
import time
from sqlalchemy import inspect, text
from app.core.database import engine as db_engine
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

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
                if e.code == 429 and attempt < max_retries - 1:
                    logger.warning(f"Gemini API rate limited (429). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
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

    def generate_action_plan(self, text_input: str) -> dict:
        logger.info(f"LLMEngine: Processing prompt: {text_input}")
        db_state = self.get_db_state()
        
        prompt = f"""
You are the database planning engine for a shop inventory app named "Vita".
Your job is to parse the user's request and output a JSON object containing:
1. "language": Detect the language and script of the user's input (e.g. English, Hinglish, Spanish, Telugu, Telugu-English mixed, etc.).
2. "intent": A brief description of what the user wants to do.
3. "operations": A list of database operations to modify the database.
4. "response": A draft friendly response in the user's same language and script.

Small businesses use this to track imports (adding items/stock) and sales (sold items, which decreases stock).

The main table to use is "inventory", which must have these columns:
- id: integer (primary key)
- item_name: string (unique name of the product, e.g., "Bananas", "Apples")
- quantity: integer (current count in stock)
- status: string (either "In Stock" if quantity > 0 else "Out of Stock")

Here is the current state of the database:
{json.dumps(db_state, indent=2)}

User request: "{text_input}"

Decide whether to CREATE the "inventory" table first if it does not exist in the current state.
If adding/importing items:
- If the item exists in "inventory", update quantity by adding new quantity.
- If it does not exist, insert a new record.
If recording sales:
- If the item exists, update quantity by subtracting the sold quantity. Ensure quantity >= 0.
- If not, explain in response that item was not found.
If deleting/removing specific items (e.g. "remove eggs"):
- Output a "delete" operation with "conditions" containing the item_name (e.g. {"item_name": "Eggs"}).
- After successful delete respond exactly: "<Item Name> removed from inventory." (e.g., "Eggs removed from inventory.")
If the user asks to clear all, delete everything, or remove all items:
- Set "confirmation_required": true instead of generating SQL/operations.

Multilingual Rules:
- Let Gemini detect the input language.
- Always respond in the same language and script as the user's input.
- Preserve mixed-language conversations (e.g., Hinglish, Telugu-English) exactly in the response.
- Never translate unless explicitly requested.

Generate the action plan. Output format must be EXACTLY:
{{
  "language": "detected language",
  "intent": "user intent description",
  "confirmation_required": false,
  "operations": [
    {{
      "type": "create_table" | "insert" | "update" | "delete" | "select" | "alter_table",
      "target": "table_name",
      "data": {{}},
      "conditions": {{}},
      "columns": []
    }}
  ],
  "response": "draft friendly response in user's detected language and script"
}}

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

    def generate_multimodal_plan(self, text_prompt: str, image_bytes: bytes, mime_type: str) -> dict:
        import base64
        logger.info("LLMEngine: Processing multimodal prompt...")
        db_state = self.get_db_state()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
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

Here is the current state of the database:
{json.dumps(db_state, indent=2)}

User instruction: "{text_prompt}"

Identify product names and quantities visible in the image.
If item exists, update quantity (adding imports, subtracting sales).
If item does not exist, insert it. Ensure table "inventory" is created if it does not exist.
If deleting/removing specific items (e.g. "remove eggs"):
- Output a "delete" operation with "conditions" containing the item_name (e.g. {"item_name": "Eggs"}).
- After successful delete respond exactly: "<Item Name> removed from inventory." (e.g., "Eggs removed from inventory.")
If the user asks to clear all, delete everything, or remove all items:
- Set "confirmation_required": true instead of generating SQL/operations.

Multilingual Rules:
- Let Gemini detect the input language.
- Always respond in the same language and script as the user's input.
- Preserve mixed-language conversations (e.g., Hinglish, Telugu-English) exactly in the response.
- Never translate unless explicitly requested.

Generate the action plan. Output format must be EXACTLY:
{{
  "language": "detected language",
  "intent": "user intent description",
  "confirmation_required": false,
  "operations": [
    {{
      "type": "create_table" | "insert" | "update" | "delete" | "select" | "alter_table",
      "target": "table_name",
      "data": {{}},
      "conditions": {{}},
      "columns": []
    }}
  ],
  "response": "draft friendly response in user's detected language and script"
}}

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

    def generate_final_response(self, user_message: str, language: str, intent: str, execution_results: list, draft_response: str) -> str:
        logger.info(f"LLMEngine: Generating final response for user in language: {language}")
        prompt = f"""
You are the assistant for the shop inventory app named "Vita".
The user said: "{user_message}"
The detected language of the conversation is: "{language}"
The parsed intent is: "{intent}"
We executed the database operations and got the following results:
{json.dumps(execution_results, indent=2)}

Draft response was: "{draft_response}"

Generate the final friendly response to the user.
Requirements:
1. Always respond in the detected language ("{language}") and script.
2. Preserve mixed-language styles (e.g., Hinglish, Telugu-English) exactly as the user used.
3. Do not translate.
4. Integrate the execution results accurately (e.g. state what was added, sold, or display queried database records if any).
5. If the draft response explicitly says "<Item> removed from inventory.", you MUST preserve that EXACT phrase.
6. Only return the plain text message, no JSON wrapping. Do not wrap the response in quotes or anything else. Just the response text.
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            response_data = self._send_request_with_retry(req)
            response_text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return response_text
        except Exception as e:
            logger.error(f"Failed to generate final response: {e}")
            return draft_response

llm_engine = LLMEngine()
