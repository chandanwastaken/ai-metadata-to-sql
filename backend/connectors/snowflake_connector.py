from .base_connector import BaseConnector
from typing import List, Dict
class SnowflakeConnector(BaseConnector):
    def connect(self):
        raise NotImplementedError("snowflake connector not implemented. Please use PostgreSQL for now.")
    def extract_metadata(self) -> List[Dict]:
        raise NotImplementedError("snowflake connector not implemented. Please use PostgreSQL for now.")
