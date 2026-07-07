import logging

logger = logging.getLogger(__name__)

class Validator:
    """
    Validates operations before they reach the executor to prevent SQL injection or schema corruption.
    Enforces standard schema constraints.
    """
    def validate(self, operations: list) -> list:
        logger.info("Validator: Validating operations against standard schema constraints...")
        valid_ops = []
        
        for op in operations:
            op_type = op.get("type", "")
            target = op.get("target", "")
            
            if not target:
                raise ValueError("Operation target (table name) is missing.")
                
            # Table name sanitization / validation
            cleaned_target = "".join([c for c in target if c.isalnum() or c == "_"])
            if not cleaned_target or cleaned_target != target:
                raise ValueError(f"Invalid table name format: '{target}'. Table name must be alphanumeric/underscores.")
            
            # Enforce standardized type values
            if op_type == "create_table":
                cols = op.get("columns", [])
                if not cols:
                    raise ValueError("Cannot create table without columns defined in 'columns' field.")
                # Basic check on column definitions
                for col in cols:
                    if not isinstance(col, dict) or "name" not in col or "type" not in col:
                        raise ValueError("Invalid column definition. Each column must have 'name' and 'type'.")
                valid_ops.append(op)
                
            elif op_type == "insert":
                if not op.get("data"):
                    raise ValueError("Cannot insert empty data records.")
                valid_ops.append(op)
                
            elif op_type == "update":
                if not op.get("data"):
                    raise ValueError("Update operation is missing update 'data'.")
                if not op.get("conditions"):
                    raise ValueError("Update operation must specify a 'conditions' filter.")
                valid_ops.append(op)
                
            elif op_type == "delete":
                if not op.get("conditions"):
                    raise ValueError("Delete operation must specify a 'conditions' filter to prevent table truncation.")
                valid_ops.append(op)
                
            elif op_type == "select":
                valid_ops.append(op)
                
            elif op_type == "alter_table":
                cols = op.get("columns", [])
                if not cols:
                    raise ValueError("Alter table operation must specify columns to add/modify.")
                valid_ops.append(op)
                
            else:
                raise ValueError(f"Unsupported operation type: '{op_type}'. Supported: create_table, insert, update, delete, select, alter_table.")
                
        return valid_ops

validator = Validator()
