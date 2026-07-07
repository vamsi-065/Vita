import logging

logger = logging.getLogger(__name__)

class Validator:
    """
    Validates operations before they reach the executor to prevent SQL injection or schema corruption.
    """
    def validate(self, operations: list) -> list:
        logger.info("Validator validating operations...")
        valid_ops = []
        for op in operations:
            op_type = op.get("type")
            
            if op_type == "create_table":
                # Validate table name
                target = op.get("target", "")
                if not target.isalnum() and "_" not in target:
                    logger.warning(f"Invalid table name: {target}. Stripping non-alphanumeric.")
                    target = "".join([c for c in target if c.isalnum() or c == "_"])
                    op["target"] = target
                
                # Validate columns
                schema = op.get("schema", {})
                cols = schema.get("columns", [])
                if not cols:
                    raise ValueError("Cannot create table without columns.")
                    
                valid_ops.append(op)
                
            elif op_type == "insert_record":
                # Ensure data is present
                if not op.get("data"):
                    raise ValueError("Cannot insert empty data.")
                valid_ops.append(op)
            else:
                logger.warning(f"Unknown operation type: {op_type}, skipping.")
                
        return valid_ops

validator = Validator()
