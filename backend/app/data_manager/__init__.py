import logging

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages CRUD operations on dynamically defined schemas.
    """
    def __init__(self):
        self.data_store = {}

    def insert(self, entity_name: str, record: dict):
        logger.info(f"Inserting into {entity_name}")
        if entity_name not in self.data_store:
            self.data_store[entity_name] = []
        self.data_store[entity_name].append(record)
        return {"status": "success", "record": record}

    def fetch(self, entity_name: str):
        return self.data_store.get(entity_name, [])

data_manager = DataManager()
