from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel, Field
import json
import re
import logging
import traceback
from datetime import datetime
from time import time
from sqlalchemy import inspect, text
from app.core.database import engine, database_service, Base
from app.llm.engine import llm_engine, RateLimitExceeded
from app.intent_normalizer import IntentNormalizer
from app.validator import validator
from app.executor import executor
from app.services.sql_generator import SQLGenerator
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

_pending_action = {}

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    message: str
    operations_executed: list = []
    data_payload: dict = None
    confirmation_required: bool = False

def get_inventory_data(user_id: str):
    try:
        inspector = inspect(engine)
        if "inventory" in inspector.get_table_names():
            with engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM inventory WHERE user_id = :uid ORDER BY id DESC"), {"uid": user_id})
                rows = []
                for row in result.mappings():
                    d = dict(row)
                    d.pop("user_id", None)
                    rows.append(d)
                return rows
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
    return []

def normalize_column_name(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r'[\s\-]+', '_', n)
    n = re.sub(r'[^a-z0-9_]', '', n)
    return n

def infer_sql_type(val) -> str:
    if isinstance(val, bool):
        return "BOOLEAN"
    if isinstance(val, (int, float)):
        if isinstance(val, int):
            return "INTEGER"
        return "NUMERIC"
    
    val_str = str(val).strip()
    if val_str.lower() in ('true', 'false'):
        return "BOOLEAN"
    
    try:
        int(val_str)
        return "INTEGER"
    except ValueError:
        pass
        
    try:
        float(val_str)
        return "NUMERIC"
    except ValueError:
        pass
        
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y'):
        try:
            datetime.strptime(val_str, fmt)
            return "DATE"
        except ValueError:
            pass
            
    return "TEXT"

def check_and_evolve_schema(operations: list):
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "inventory" not in table_names:
        return
        
    existing_cols = {col['name'] for col in inspector.get_columns('inventory')}
    schema_updated = False
    
    for op in operations:
        if op.get("target") != "inventory":
            continue
            
        data = op.get("data")
        if isinstance(data, dict):
            normalized_data = {}
            for k, v in data.items():
                norm_k = normalize_column_name(k)
                normalized_data[norm_k] = v
                
                if norm_k not in existing_cols:
                    col_type = infer_sql_type(v)
                    logger.info(f"Dynamic Schema Evolution: Adding column '{norm_k}' of type '{col_type}' to inventory table.")
                    with database_service.transaction() as session:
                        session.execute(text(f"ALTER TABLE inventory ADD COLUMN {norm_k} {col_type};"))
                    existing_cols.add(norm_k)
                    schema_updated = True
            op["data"] = normalized_data

        conditions = op.get("conditions")
        if isinstance(conditions, dict):
            normalized_conditions = {}
            for k, v in conditions.items():
                norm_k = normalize_column_name(k)
                normalized_conditions[norm_k] = v
                
                if norm_k not in existing_cols:
                    col_type = infer_sql_type(v)
                    logger.info(f"Dynamic Schema Evolution (Conditions): Adding column '{norm_k}' of type '{col_type}' to inventory table.")
                    with database_service.transaction() as session:
                        session.execute(text(f"ALTER TABLE inventory ADD COLUMN {norm_k} {col_type};"))
                    existing_cols.add(norm_k)
                    schema_updated = True
            op["conditions"] = normalized_conditions

    if schema_updated:
        try:
            logger.info("Dynamic Schema Evolution: Refreshing SQLAlchemy metadata and connections.")
            engine.dispose()
            Base.metadata.clear()
            try:
                Base.metadata.reflect(bind=engine)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error resetting SQLAlchemy metadata after schema change: {e}")

def run_pipeline(request_message: str, action_plan: dict, user_id: str):
    start_time = time()
    logger.info("=================== PIPELINE START ===================")
    logger.info(f"Stage 1: User Prompt: {request_message}")
    logger.info(f"Stage 2: Gemini Response / Parsed Intent: {json.dumps(action_plan)}")

    if action_plan.get("confirmation_required"):
        logger.info("Stage 3: Confirmation Required - skipping execution.")
        
        global _pending_action
        _pending_action[user_id] = {"type": "DELETE_ALL_INVENTORY"}
        
        draft_response = action_plan.get("response") or action_plan.get("message") or "Are you sure you want to clear all items? Please confirm."
        return {
            "message": draft_response,
            "operations_executed": [],
            "data_payload": {
                "added_items": [],
                "total_inventory": get_inventory_data(user_id)
            },
            "confirmation_required": True
        }

    # 1. Normalization
    try:
        normalized_plan = IntentNormalizer.normalize(action_plan)
        normalized_ops = normalized_plan.get("operations", [])
        logger.info(f"Stage 3: Normalized Intent: {json.dumps(normalized_ops)}")
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[PIPELINE ERROR] Normalization Stage Failed:\n{error_details}")
        raise HTTPException(status_code=400, detail="Intent Normalization failed. Check server logs.")

    # 2. Validation
    try:
        valid_ops = validator.validate(normalized_ops)
        logger.info(f"Stage 4: Validation Result: Successfully validated {len(valid_ops)} operations.")
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[PIPELINE ERROR] Validation Stage Failed:\n{error_details}")
        raise HTTPException(status_code=400, detail="Intent Validation failed. Check server logs.")

    # Dynamic Schema Evolution check
    try:
        check_and_evolve_schema(valid_ops)
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[PIPELINE ERROR] Schema Evolution Stage Failed:\n{error_details}")
        raise HTTPException(status_code=400, detail="Schema Evolution failed. Check server logs.")

    # 3. Check for mutative command mismatch
    mutative_keywords = ["add", "sell", "update", "delete", "create", "insert", "remove", "modify", "clear"]
    is_mutative = any(kw in request_message.lower() for kw in mutative_keywords)
    if is_mutative and not valid_ops:
        draft = normalized_plan.get("response") or normalized_plan.get("message", "")
        if draft:
            logger.info(f"Mutative request yielded 0 operations, but LLM provided response: {draft}")
        else:
            logger.error("[PIPELINE ERROR] Mutative request detected but parsed 0 valid database operations.")
            raise HTTPException(status_code=400, detail="Failed to parse user intent into database operations.")

    # 3.5 Strict Stock Validation
    inventory_data = get_inventory_data(user_id)
    for op in valid_ops:
        if op.get("type") == "update" and op.get("target") == "inventory":
            item_name = op.get("conditions", {}).get("item_name")
            new_quantity = op.get("data", {}).get("quantity")
            requested_deduction = op.get("meta", {}).get("requested_deduction")
            
            if item_name:
                current_item = next((item for item in inventory_data if item["item_name"].lower() == item_name.lower()), None)
                if current_item:
                    current_stock = current_item["quantity"]
                    
                    # Deduce requested_amount if meta was not provided, but new_quantity went negative
                    if requested_deduction is None and new_quantity is not None and new_quantity < 0:
                        requested_deduction = current_stock - new_quantity

                    if requested_deduction is not None and requested_deduction > current_stock:
                        error_msg = f"Cannot remove {requested_deduction} {current_item['item_name']}. Only {current_stock} are available in stock."
                        return {
                            "message": error_msg,
                            "operations_executed": [],
                            "data_payload": {
                                "added_items": [],
                                "total_inventory": inventory_data,
                                "queried_data": []
                            },
                            "confirmation_required": False
                        }

    # 4. Database Transaction, SQL Generation & Execution
    execution_results = []
    try:
        with database_service.transaction() as session:
            for op in valid_ops:
                # SQL Generation
                sql, params = SQLGenerator.generate(op)
                logger.info(f"Stage 5: Generated SQL: {sql} | Parameters: {params}")
                
                # Execution
                res = executor.execute_ops(session, [op], user_id=user_id)
                execution_results.extend(res)
                logger.info(f"Stage 6: SQL Execution Success: {res}")
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"[PIPELINE ERROR] SQL Generation / Execution Stage Failed:\n{error_details}")
        raise HTTPException(status_code=400, detail="Database execution failed. Check server logs.")

    duration = time() - start_time
    logger.info(f"Stage 7: Pipeline Duration: {duration:.3f}s")
    logger.info("==================== PIPELINE END ====================")

    language = normalized_plan.get("language", "English")
    intent = normalized_plan.get("intent", "")
    draft_response = normalized_plan.get("response") or normalized_plan.get("message", "")

    queried_data = []
    formatted_execution_results = []
    error_message = None
    for res in execution_results:
        if isinstance(res, dict):
            if res.get("type") == "select":
                queried_data.extend(res.get("data", []))
                formatted_execution_results.append(f"Selected {len(res.get('data', []))} records.")
            elif res.get("type") == "error":
                error_message = res.get("message", "Error")
                formatted_execution_results.append(error_message)
        else:
            formatted_execution_results.append(str(res))

    response_msg = draft_response
    if error_message:
        response_msg = error_message
    elif not response_msg:
        if not formatted_execution_results:
            response_msg = "I couldn't understand any executable operations in your request."
        else:
            response_msg = (
                f"Successfully executed the following operations:\n"
                + "\n".join([f"- {res}" for res in formatted_execution_results])
            )

    has_select_op = any(op.get("type") == "select" for op in valid_ops)
    if has_select_op and not queried_data:
        response_msg = "No matching products found."

    added_items = []
    for op in valid_ops:
        if op.get("type") in ["insert", "update"] and op.get("target") == "inventory":
            added_items.append(op.get("data", {}))

    return {
        "message": response_msg,
        "operations_executed": valid_ops,
        "data_payload": {
            "added_items": added_items,
            "total_inventory": get_inventory_data(user_id),
            "queried_data": queried_data
        }
    }

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    global _pending_action
    logger.info(f"Initiated chat request: {request.message}")
    
    msg_lower = request.message.strip().lower()
    pending = _pending_action.get(user_id)
    if pending and pending.get("type") == "DELETE_ALL_INVENTORY":
        if msg_lower in ["yes", "y", "confirm", "proceed", "continue"]:
            logger.info("User confirmed pending DELETE_ALL_INVENTORY action.")
            try:
                with database_service.transaction() as session:
                    session.execute(text("DELETE FROM inventory WHERE user_id = :uid;"), {"uid": user_id})
                _pending_action.pop(user_id, None)
                return {
                    "message": "Inventory cleared successfully.",
                    "operations_executed": [{"type": "delete_all", "target": "inventory"}],
                    "data_payload": {
                        "added_items": [],
                        "total_inventory": get_inventory_data(user_id)
                    },
                    "confirmation_required": False
                }
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Failed to execute confirmed delete_all:\n{error_details}")
                raise HTTPException(status_code=500, detail="Failed to clear inventory. Check server logs.")
        elif msg_lower in ["no", "cancel", "n"]:
            logger.info("User cancelled pending DELETE_ALL_INVENTORY action.")
            _pending_action.pop(user_id, None)
            return {
                "message": "Operation cancelled.",
                "operations_executed": [],
                "data_payload": {
                    "added_items": [],
                    "total_inventory": get_inventory_data(user_id)
                },
                "confirmation_required": False
            }
        else:
            # If they reply with something else entirely, clear pending state and process normally.
            _pending_action.pop(user_id, None)

    # 1. Call Gemini to parse intent
    try:
        action_plan = llm_engine.generate_action_plan(request.message, user_id)
    except RateLimitExceeded as e:
        logger.error(f"Gemini API Rate Limit Exceeded: {e}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Gemini API failure during action plan generation:\n{error_details}")
        raise HTTPException(status_code=400, detail="AI engine communication failure. Check server logs.")
        
    # 2. Run the intent resolution and database pipeline
    return run_pipeline(request.message, action_plan, user_id)

@router.post("/upload", response_model=ChatResponse)
async def upload(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    logger.info(f"Uploaded file: {file.filename}")
    
    image_bytes = await file.read()
    mime_type = file.content_type or "image/png"
    
    # 1. Call Gemini multimodal models to parse intent
    try:
        action_plan = llm_engine.generate_multimodal_plan(
            text_prompt="Please analyze this document/photo and update the inventory.",
            image_bytes=image_bytes,
            mime_type=mime_type,
            user_id=user_id
        )
    except RateLimitExceeded as e:
        logger.error(f"Gemini API Rate Limit Exceeded: {e}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Gemini Multimodal API failure:\n{error_details}")
        raise HTTPException(status_code=400, detail="AI engine communication failure. Check server logs.")
        
    # 2. Run the intent resolution and database pipeline
    return run_pipeline(f"Upload: {file.filename}", action_plan, user_id)
