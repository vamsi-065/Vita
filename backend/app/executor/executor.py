import logging
from sqlalchemy.orm import Session
from app.services.sql_generator import SQLGenerator
from app.repositories.dynamic_repository import DynamicRepository

logger = logging.getLogger(__name__)

class Executor:
    """
    Executes DDL and DML operations securely via parameterized dynamic repository queries.
    """
    def execute_ops(self, session: Session, operations: list) -> list:
        logger.info(f"Executor: Executing {len(operations)} operations...")
        results = []
        repo = DynamicRepository(session)
        
        for op in operations:
            op_type = op.get("type", "")
            target = op.get("target", "")
            
            # Generate parameterized SQL and mapping parameters
            sql, params = SQLGenerator.generate(op)
            
            # Execute SQL within the session transaction boundary
            res = repo.execute_statement(sql, params)
            
            # Get count of affected rows
            row_count = res.rowcount if hasattr(res, "rowcount") else None
            
            if op_type == "create_table":
                results.append(f"Successfully created table '{target}'.")
            elif op_type == "insert":
                results.append(f"Inserted record into '{target}'.")
            elif op_type == "update":
                results.append(f"Updated {row_count if row_count is not None else 0} records in '{target}'.")
            elif op_type == "delete":
                results.append(f"Deleted {row_count if row_count is not None else 0} records from '{target}'.")
            elif op_type == "alter_table":
                results.append(f"Altered table structure for '{target}'.")
            elif op_type == "select":
                results.append(f"Selected records from '{target}'.")
                
        return results

executor = Executor()
