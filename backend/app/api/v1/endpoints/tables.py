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
def list_tables():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    tables = []
    for name in table_names:
        tables.append(TableSummary(name=name, created_at=datetime.utcnow()))
    return {"tables": tables}

@router.post("/clean")
def clean_inventory():
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("TRUNCATE TABLE inventory RESTART IDENTITY CASCADE;"))
        return {"status": "success", "message": "Database cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@router.get("/{table_name}", response_model=TableDetailResponse)
def get_table(table_name: str):
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if table_name not in table_names:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    columns_info = inspector.get_columns(table_name)
    columns = []
    for col in columns_info:
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
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
            rows = [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading table rows: {str(e)}")
        
    return {
        "table": table_name,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows)
    }
