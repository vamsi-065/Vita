import logging

logger = logging.getLogger(__name__)

class Planner:
    """
    Takes a structured JSON Action Plan from the LLM and sequences it into iterable operations.
    """
    def sequence_plan(self, action_plan: dict) -> list:
        logger.info("Planner sequencing action plan...")
        
        operations = action_plan.get("operations", [])
        # We can add dependency resolution here if needed.
        # For now, we assume the LLM ordered them correctly.
        
        sequenced_ops = []
        for op in operations:
            sequenced_ops.append(op)
            
        return sequenced_ops

planner = Planner()
