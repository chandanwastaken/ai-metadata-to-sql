from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from typing import Tuple
import sqlparse
from utils import is_destructive
def validate_sql(sql: str) -> Tuple[bool, str]:
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, 'No valid SQL detected'
        if is_destructive(sql):
            return False, 'Destructive SQL statements are disallowed.'
        return True, ''
    except Exception as e:
        return False, str(e)
def execute_sql(conn_str: str, sql: str, limit: int = 1000) -> Tuple[pd.DataFrame, str]:
    valid, msg = validate_sql(sql)
    if not valid:
        raise ValueError(f'SQL Validation failed: {msg}')
    engine = create_engine(conn_str)
    sql_to_run = sql
    if 'LIMIT' not in sql.upper() and sql.strip().upper().startswith('SELECT'):
        sql_to_run = sql.rstrip(';') + f' LIMIT {limit};'
    try:
        with engine.connect() as conn:
            res = conn.execute(text(sql_to_run))
            df = pd.DataFrame(res.fetchall(), columns=res.keys())
            return df, sql_to_run
    except SQLAlchemyError as e:
        raise
