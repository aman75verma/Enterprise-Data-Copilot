import os
import re
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://copilot:copilot_pass@localhost:5433/copilot_db")
FORBIDDEN_SQL = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|call)\b", re.I)


class UnsafeQueryError(ValueError):
    pass


def _without_string_literals(sql_query: str) -> str:
    return re.sub(r"('([^']|'')*'|\"([^\"]|\"\")*\")", "", sql_query)


def validate_select_query(sql_query: str) -> str:
    normalized = sql_query.strip()
    if not normalized:
        raise UnsafeQueryError("SQL query cannot be empty")

    if normalized.endswith(";"):
        normalized = normalized[:-1].strip()

    if ";" in normalized:
        raise UnsafeQueryError("Only one SELECT statement is allowed")

    if not re.match(r"^select\b", normalized, re.I):
        raise UnsafeQueryError("Only read-only SELECT queries are allowed")

    if FORBIDDEN_SQL.search(_without_string_literals(normalized)):
        raise UnsafeQueryError("Query contains a forbidden write/admin keyword")

    return normalized


def query_customer_db(sql_query: str, max_rows: int = 100) -> dict[str, Any]:
    safe_query = validate_select_query(sql_query)

    with psycopg2.connect(DATABASE_URL) as conn:
        conn.set_session(readonly=True, autocommit=False)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout = 5000")
            cur.execute(safe_query)
            rows = cur.fetchmany(max_rows + 1)

    visible_rows = rows[:max_rows]
    return {
        "columns": list(visible_rows[0].keys()) if visible_rows else [],
        "rows": [dict(row) for row in visible_rows],
        "row_count": len(visible_rows),
        "truncated": len(rows) > max_rows,
    }
