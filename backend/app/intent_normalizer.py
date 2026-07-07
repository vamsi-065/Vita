import logging

logger = logging.getLogger(__name__)

class IntentNormalizer:
    @staticmethod
    def normalize_operation(op: dict) -> dict:
        if not isinstance(op, dict):
            return {
                "type": "",
                "target": "",
                "data": {},
                "conditions": {},
                "columns": []
            }
            
        # Extract and normalize operation type
        op_type = op.get("type") or op.get("operation_type") or op.get("op_type") or ""
        if isinstance(op_type, str):
            op_type = op_type.lower().strip()
        else:
            op_type = ""
        
        # Standardize operation type strings
        if op_type in ["insert_record", "insert"]:
            op_type = "insert"
        elif op_type in ["update_record", "update"]:
            op_type = "update"
        elif op_type in ["delete_record", "delete"]:
            op_type = "delete"
        elif op_type in ["select_record", "select"]:
            op_type = "select"
        elif op_type in ["create_table", "create"]:
            op_type = "create_table"
        elif op_type in ["alter_table", "alter"]:
            op_type = "alter_table"

        # Extract and normalize target table name
        target = op.get("target") or op.get("table_name") or op.get("table") or ""
        if isinstance(target, str):
            target = target.lower().strip()
        else:
            target = ""

        # Extract values / data
        data = op.get("data") or op.get("record") or op.get("values") or {}
        if not isinstance(data, dict):
            data = {}

        # Extract conditions / filters
        conditions = op.get("conditions") or op.get("where") or op.get("filter") or {}
        if not isinstance(conditions, dict):
            conditions = {}

        # Extract columns schema list
        columns = op.get("columns") or op.get("schema", {}).get("columns", []) or []
        if not isinstance(columns, list):
            columns = []

        normalized = {
            "type": op_type,
            "target": target,
            "data": data,
            "conditions": conditions,
            "columns": columns
        }
        logger.info(f"IntentNormalizer: Normalized legacy operation to standard format: {normalized}")
        return normalized

    @staticmethod
    def normalize(plan: dict) -> dict:
        normalized_plan = {
            "message": plan.get("message", "") or plan.get("response", ""),
            "response": plan.get("response", "") or plan.get("message", ""),
            "language": plan.get("language", "English"),
            "intent": plan.get("intent", ""),
        }
        raw_ops = plan.get("operations", [])
        if not isinstance(raw_ops, list):
            raw_ops = []
            
        normalized_plan["operations"] = [IntentNormalizer.normalize_operation(op) for op in raw_ops]
        return normalized_plan
