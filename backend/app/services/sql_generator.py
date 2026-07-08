import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    @staticmethod
    def map_type(col_type: str) -> str:
        t = col_type.lower().strip()
        if t in ["integer", "int"]:
            return "INTEGER"
        elif t in ["string", "varchar", "text"]:
            return "VARCHAR(255)"
        elif t in ["boolean", "bool"]:
            return "BOOLEAN"
        elif t in ["float", "double", "real"]:
            return "DOUBLE PRECISION"
        return "VARCHAR(255)"

    @staticmethod
    def generate(op: dict) -> tuple[str, dict]:
        op_type = op.get("type", "")
        target = op.get("target", "").lower().strip()
        
        sql = ""
        params = {}
        
        if op_type == "create_table":
            col_defs = []
            for col in op.get("columns", []):
                col_name = col["name"].lower().strip()
                col_type = SQLGenerator.map_type(col["type"])
                
                # Automatically map id to SERIAL PRIMARY KEY
                if col_name == "id" and col_type == "INTEGER":
                    col_defs.append("id SERIAL PRIMARY KEY")
                else:
                    col_defs.append(f"{col_name} {col_type}")
            
            sql = f"CREATE TABLE IF NOT EXISTS {target} ({', '.join(col_defs)});"
            
        elif op_type == "insert":
            data = op.get("data", {})
            columns = []
            placeholders = []
            for col, val in data.items():
                col_clean = col.lower().strip()
                columns.append(col_clean)
                placeholders.append(f":{col_clean}")
                params[col_clean] = val
                
            sql = f"INSERT INTO {target} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
            
        elif op_type == "update":
            data = op.get("data", {})
            conditions = op.get("conditions", {})
            
            set_clauses = []
            for col, val in data.items():
                col_clean = col.lower().strip()
                param_name = f"set_{col_clean}"
                set_clauses.append(f"{col_clean} = :{param_name}")
                params[param_name] = val
                
            where_clauses = []
            for col, val in conditions.items():
                col_clean = col.lower().strip()
                param_name = f"cond_{col_clean}"
                where_clauses.append(f"{col_clean} = :{param_name}")
                params[param_name] = val
                
            where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            sql = f"UPDATE {target} SET {', '.join(set_clauses)}{where_str};"
            
        elif op_type == "delete":
            conditions = op.get("conditions", {})
            where_clauses = []
            for col, val in conditions.items():
                col_clean = col.lower().strip()
                param_name = f"cond_{col_clean}"
                if isinstance(val, str):
                    where_clauses.append(f"LOWER({col_clean}) = LOWER(:{param_name})")
                else:
                    where_clauses.append(f"{col_clean} = :{param_name}")
                params[param_name] = val
                
            if not where_clauses:
                raise ValueError("DELETE operation must specify a WHERE clause.")
                
            where_str = f" WHERE {' AND '.join(where_clauses)}"
            sql = f"DELETE FROM {target}{where_str};"
            
        elif op_type == "delete_all":
            sql = f"DELETE FROM {target};"
            
        elif op_type == "select":
            conditions = op.get("conditions", {})
            where_clauses = []
            for col, val in conditions.items():
                col_clean = col.lower().strip()
                param_name = f"cond_{col_clean}"
                where_clauses.append(f"{col_clean} = :{param_name}")
                params[param_name] = val
                
            where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            sql = f"SELECT * FROM {target}{where_str};"
            
        elif op_type == "alter_table":
            columns = op.get("columns", [])
            alter_clauses = []
            for col in columns:
                col_name = col["name"].lower().strip()
                col_type = SQLGenerator.map_type(col["type"])
                alter_clauses.append(f"ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                
            sql = f"ALTER TABLE {target} {', '.join(alter_clauses)};"
            
        logger.info(f"SQLGenerator: Generated parameterized query: {sql} with parameters: {params}")
        return sql, params
