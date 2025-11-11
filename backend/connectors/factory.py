from .postgres_connector import PostgresConnector
from .oracle_connector import OracleConnector
from .snowflake_connector import SnowflakeConnector
from .teradata_connector import TeradataConnector
from .db2_connector import DB2Connector
def get_connector(db_type: str, connection_string: str, schema: str):
    mapping = {
        'postgresql': PostgresConnector,
        'postgres': PostgresConnector,
        'pg': PostgresConnector,
        'oracle': OracleConnector,
        'snowflake': SnowflakeConnector,
        'teradata': TeradataConnector,
        'db2': DB2Connector
    }
    key = (db_type or '').lower()
    if key not in mapping:
        raise ValueError(f'Unsupported or unimplemented database type: {db_type}')
    return mapping[key](connection_string, schema)
