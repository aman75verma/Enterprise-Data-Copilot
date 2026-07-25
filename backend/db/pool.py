"""
Shared database connection pool.

All tools import `get_connection()` instead of calling `psycopg2.connect()` directly.
This avoids creating a new TCP connection on every request.
"""

import os

import psycopg2
import psycopg2.pool
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://copilot:copilot_pass@localhost:5433/copilot_db")

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
        )
    return _pool


def get_connection():
    """Get a connection from the pool. Caller must call `put_connection()` when done."""
    return _get_pool().getconn()


def put_connection(conn):
    """Return a connection to the pool."""
    _get_pool().putconn(conn)


def close_pool():
    """Shut down the pool (call on app shutdown)."""
    global _pool
    if _pool and not _pool.closed:
        _pool.closeall()
        _pool = None
