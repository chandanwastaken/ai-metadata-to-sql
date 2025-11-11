import re
from typing import List
DANGEROUS_SQL_PATTERNS = [r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b", r"\bTRUNCATE\b", r"\bUPDATE\b"]
def is_destructive(sql: str) -> bool:
    sql_up = sql.upper()
    return any(re.search(pat, sql_up) for pat in DANGEROUS_SQL_PATTERNS)
def sanitize_identifier(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z_\-]", "_", s)
