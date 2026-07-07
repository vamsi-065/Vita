import os
import json
import logging

logger = logging.getLogger(__name__)

class LLMEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        
    def generate_action_plan(self, text: str) -> dict:
        """
        Takes natural language and converts it to a structured JSON Action Plan.
        """
        logger.info(f"LLM Engine processing: {text}")
        text_lower = text.lower()
        
        # Fallback Mock logic when no real LLM API key is present.
        # In production, this would call a real LLM (like Gemini) with a strict JSON schema prompt.
        
        if "create" in text_lower and "table" in text_lower:
            target = "new_table"
            words = text_lower.replace(',', '').split()
            
            if "table" in words:
                idx = words.index("table")
                if idx + 1 < len(words) and words[idx + 1] != "with":
                    target = words[idx + 1]
                elif idx > 0 and words[idx - 1] not in ["a", "create"]:
                    target = words[idx - 1]
            
            # Extract basic columns if specified, else default
            columns = [{"name": "id", "type": "integer", "primary_key": True}]
            if "columns" in words:
                col_idx = words.index("columns")
                raw_cols = words[col_idx + 1:]
                for c in raw_cols:
                    if c not in ["and", "with"]:
                        columns.append({"name": c, "type": "string", "nullable": True})
            else:
                columns.append({"name": "name", "type": "string", "nullable": False})
            
            return {
                "operations": [
                    {
                        "type": "create_table",
                        "target": target,
                        "schema": {
                            "columns": columns
                        }
                    }
                ]
            }
            
        # Default empty plan if unrecognized
        return {"operations": []}

llm_engine = LLMEngine()
