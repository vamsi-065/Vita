from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from sqlalchemy import inspect, text

from app.core.database import engine
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class TableSummary(BaseModel):
    name: str
    created_at: datetime

class TablesListResponse(BaseModel):
    tables: List[TableSummary]

class ColumnMeta(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool = False
    unique: bool = False

class TableDetailResponse(BaseModel):
    table: str
    columns: List[ColumnMeta]
    rows: List[dict]
    row_count: int

@router.get("/", response_model=TablesListResponse)
def list_tables(current_user = Depends(get_current_user)):
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    tables = []
    for name in table_names:
        columns = [c['name'] for c in inspector.get_columns(name)]
        if "user_id" in columns:
            tables.append(TableSummary(name=name, created_at=datetime.utcnow()))
    return {"tables": tables}

@router.post("/clean")
def clean_inventory(current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("DELETE FROM inventory WHERE user_id = :uid;"), {"uid": user_id})
        return {"status": "success", "message": "Database cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@router.get("/{table_name}", response_model=TableDetailResponse)
def get_table(table_name: str, current_user = Depends(get_current_user)):
    user_id = str(current_user.id)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if table_name not in table_names:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    columns_info = inspector.get_columns(table_name)
    column_names = [c['name'] for c in columns_info]
    
    if "user_id" not in column_names:
        raise HTTPException(status_code=403, detail="Access denied")
        
    columns = []
    for col in columns_info:
        if col['name'] == 'user_id': continue
        columns.append(ColumnMeta(
            name=col['name'],
            type=str(col['type']),
            nullable=col['nullable'],
            primary_key=bool(col.get('primary_key', False)),
            unique=bool(col.get('unique', False))
        ))
        
    rows = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} WHERE user_id = :uid LIMIT 100"), {"uid": user_id})
            for row in result.mappings():
                d = dict(row)
                d.pop("user_id", None)
                rows.append(d)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading table rows: {str(e)}")
        
    return {
        "table": table_name,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows)
    }
