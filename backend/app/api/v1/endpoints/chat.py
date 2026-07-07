from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import json
import logging

from app.api.v1.endpoints.auth import get_current_user
from app.llm import llm_engine
from app.planner import planner
from app.validator import validator
from app.executor import executor
from app.schema_manager import schema_manager

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    message: str
    operations_executed: list = []

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, current_user = Depends(get_current_user)):
    logger.info(f"User {current_user.email} initiated chat request: {request.message}")
    
    # 1. LLM converts NL to JSON Action Plan
    action_plan_json = llm_engine.generate_action_plan(request.message)
    
    # 2. Planner sequences it
    sequenced_ops = planner.sequence_plan(action_plan_json)
    
    # 3. Validator ensures safety
    valid_ops = validator.validate(sequenced_ops)
    
    # 4. Executor runs on Database
    execution_results = executor.execute(valid_ops)
    
    # 5. Schema Refresh
    schema_manager.refresh()
    
    # 6. Response to User
    if not execution_results:
        response_msg = "I couldn't understand any executable operations in your request."
    else:
        response_msg = (
            f"Successfully executed the following operations:\n"
            + "\n".join([f"- {res}" for res in execution_results])
        )
        
    return {
        "message": response_msg,
        "operations_executed": valid_ops
    }
