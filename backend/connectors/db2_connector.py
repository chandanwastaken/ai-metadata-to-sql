from .base_connector import BaseConnector
from typing import List, Dict
class DB2Connector(BaseConnector):
    def connect(self):
        raise NotImplementedError("db2 connector not implemented. Please use PostgreSQL for now.")
    def extract_metadata(self) -> List[Dict]:
        raise NotImplementedError("db2 connector not implemented. Please use PostgreSQL for now.")
