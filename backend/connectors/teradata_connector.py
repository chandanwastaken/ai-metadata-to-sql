from .base_connector import BaseConnector
from typing import List, Dict
class TeradataConnector(BaseConnector):
    def connect(self):
        raise NotImplementedError("teradata connector not implemented. Please use PostgreSQL for now.")
    def extract_metadata(self) -> List[Dict]:
        raise NotImplementedError("teradata connector not implemented. Please use PostgreSQL for now.")
