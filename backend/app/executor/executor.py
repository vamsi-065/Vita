import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

class Executor:
    """
    Executes DDL and DML operations securely via SQLAlchemy.
    """
    def execute(self, operations: list):
        logger.info("Executor starting execution of operations...")
        results = []
        
        type_mapping = {
            "integer": "INTEGER",
            "string": "VARCHAR",
            "float": "FLOAT",
            "boolean": "BOOLEAN",
            "datetime": "DATETIME"
        }
        
        with engine.connect() as conn:
            with conn.begin():
                for op in operations:
                    op_type = op.get("type")
                    if op_type == "create_table":
                        target = op.get("target")
                        columns = op.get("schema", {}).get("columns", [])
                        
                        col_defs = []
                        for col in columns:
                            c_name = col.get("name")
                            c_type = type_mapping.get(col.get("type", "string"), "VARCHAR")
                            c_pk = "PRIMARY KEY" if col.get("primary_key") else ""
                            c_null = "NOT NULL" if not col.get("nullable", True) and not col.get("primary_key") else ""
                            
                            col_def = f"{c_name} {c_type} {c_pk} {c_null}".strip()
                            col_defs.append(col_def)
                            
                        sql = f"CREATE TABLE IF NOT EXISTS {target} ({', '.join(col_defs)});"
                        logger.info(f"Executing SQL: {sql}")
                        conn.execute(text(sql))
                        results.append(f"Created table {target}")
                        
                    elif op_type == "insert_record":
                        target = op.get("target")
                        data = op.get("data", {})
                        
                        cols = ", ".join(data.keys())
                        placeholders = ", ".join([f":{k}" for k in data.keys()])
                        
                        sql = f"INSERT INTO {target} ({cols}) VALUES ({placeholders});"
                        logger.info(f"Executing SQL: {sql}")
                        conn.execute(text(sql), data)
                        results.append(f"Inserted record into {target}")
                        
        return results

executor = Executor()
