from .base_connector import BaseConnector
from typing import List, Dict
class OracleConnector(BaseConnector):
    def connect(self):
        raise NotImplementedError("oracle connector not implemented. Please use PostgreSQL for now.")
    def extract_metadata(self) -> List[Dict]:
        raise NotImplementedError("oracle connector not implemented. Please use PostgreSQL for now.")
