from .base_connector import BaseConnector
from sqlalchemy import create_engine, inspect
from typing import List, Dict
class PostgresConnector(BaseConnector):
    def connect(self):
        self.engine = create_engine(self.connection_string)
        self.inspector = inspect(self.engine)
    def extract_metadata(self) -> List[Dict]:
        metadata_entries = []
        for table_name in self.inspector.get_table_names(schema=self.schema):
            cols = []
            for col in self.inspector.get_columns(table_name, schema=self.schema):
                cols.append({'name': col.get('name'), 'type': str(col.get('type'))})
            fks = self.inspector.get_foreign_keys(table_name, schema=self.schema)
            metadata_entries.append({
                'id': f"{self.schema}.{table_name}",
                'type': 'table',
                'name': table_name,
                'schema': self.schema,
                'columns': cols,
                'foreign_keys': fks,
                'readable': f"Table {self.schema}.{table_name}: " + ", ".join([f"{c['name']} ({c['type']})" for c in cols])
            })
        try:
            for view_name in self.inspector.get_view_names(schema=self.schema):
                cols = []
                for col in self.inspector.get_columns(view_name, schema=self.schema):
                    cols.append({'name': col.get('name'), 'type': str(col.get('type'))})
                metadata_entries.append({
                    'id': f"{self.schema}.{view_name}",
                    'type': 'view',
                    'name': view_name,
                    'schema': self.schema,
                    'columns': cols,
                    'foreign_keys': [],
                    'readable': f"View {self.schema}.{view_name}: " + ", ".join([f"{c['name']} ({c['type']})" for c in cols])
                })
        except Exception:
            pass
        return metadata_entries
