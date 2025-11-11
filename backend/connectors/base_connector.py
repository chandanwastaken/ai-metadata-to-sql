from abc import ABC, abstractmethod
from typing import List, Dict
class BaseConnector(ABC):
    def __init__(self, connection_string: str, schema: str):
        self.connection_string = connection_string
        self.schema = schema
    @abstractmethod
    def connect(self):
        pass
    @abstractmethod
    def extract_metadata(self) -> List[Dict]:
        pass
