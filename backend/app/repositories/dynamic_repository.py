import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DynamicRepository:
    def __init__(self, session: Session):
        self.session = session

    def execute_statement(self, sql: str, params: Dict[str, Any] = None) -> Any:
        logger.info(f"DynamicRepository: Executing SQL statement: {sql} with params: {params}")
        return self.session.execute(text(sql), params or {})

    def fetch_all(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        logger.info(f"DynamicRepository: Fetching all for SQL: {sql} with params: {params}")
        result = self.session.execute(text(sql), params or {})
        keys = list(result.keys())
        return [dict(zip(keys, row)) for row in result.fetchall()]

    def fetch_one(self, sql: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        logger.info(f"DynamicRepository: Fetching one for SQL: {sql} with params: {params}")
        result = self.session.execute(text(sql), params or {})
        row = result.fetchone()
        if row:
            return dict(zip(list(result.keys()), row))
        return None
