from sqlalchemy import create_engine, inspect, text
from typing import List, Dict
def extract_schema_metadata(conn_str: str, schema: str = 'public') -> List[Dict]:
    engine = create_engine(conn_str)
    inspector = inspect(engine)
    metadata_entries = []
    for table_name in inspector.get_table_names(schema=schema):
        cols = []
        for col in inspector.get_columns(table_name, schema=schema):
            cols.append({'name': col.get('name'), 'type': str(col.get('type'))})
        fks = inspector.get_foreign_keys(table_name, schema=schema)
        entry = {'id': f"{schema}.{table_name}", 'type': 'table', 'name': table_name, 'schema': schema, 'columns': cols, 'foreign_keys': fks, 'ddl': None}
        metadata_entries.append(entry)
    try:
        for view_name in inspector.get_view_names(schema=schema):
            cols = []
            for col in inspector.get_columns(view_name, schema=schema):
                cols.append({'name': col.get('name'), 'type': str(col.get('type'))})
            entry = {'id': f"{schema}.{view_name}", 'type': 'view', 'name': view_name, 'schema': schema, 'columns': cols, 'foreign_keys': [], 'ddl': None}
            metadata_entries.append(entry)
    except Exception:
        pass
    for e in metadata_entries:
        readable_cols = ", ".join([f"{c['name']} ({c['type']})" for c in e['columns']])
        e['readable'] = f"{e['type'].capitalize()} {e['schema']}.{e['name']}: {readable_cols}"
    return metadata_entries
