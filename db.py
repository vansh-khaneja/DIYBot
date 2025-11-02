"""Database utilities supporting both SQLite and Postgres backends."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Sequence, Set, Dict

try:  # Optional dependency - only needed when using Postgres
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
except ImportError:  # pragma: no cover - psycopg is optional at runtime
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore
    ConnectionPool = None  # type: ignore


POSTGRES_URL = os.environ.get("POSTGRES_DB_URL")
USING_POSTGRES = bool(POSTGRES_URL)

# Connection pool for Postgres (initialized on first use)
_postgres_pool: Optional["ConnectionPool"] = None

# Schema cache to avoid repeated information_schema queries
_schema_cache: Dict[str, Set[str]] = {}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = DATA_DIR / "workflows.db"


def _ensure_psycopg() -> None:
    if USING_POSTGRES and psycopg is None:
        raise RuntimeError(
            "psycopg is required for Postgres usage but is not installed. "
            "Install it by adding 'psycopg[binary]' to requirements.txt."
        )


def _get_postgres_pool() -> "ConnectionPool":
    """Get or create the Postgres connection pool (singleton pattern)."""
    global _postgres_pool
    
    if _postgres_pool is None:
        _ensure_psycopg()
        assert psycopg is not None and ConnectionPool is not None
        
        # Create connection pool with reasonable defaults
        # min_size: minimum connections to keep open
        # max_size: maximum connections allowed
        # timeout: how long to wait for a connection from the pool
        _postgres_pool = ConnectionPool(
            POSTGRES_URL,
            min_size=2,
            max_size=10,
            timeout=5.0,
            kwargs={
                "row_factory": dict_row,
                "autocommit": True
            }
        )
    
    return _postgres_pool


@contextmanager
def get_connection() -> Iterator["ConnectionProtocol"]:
    """Yield a database connection (Postgres pool if configured, otherwise SQLite)."""

    if USING_POSTGRES:
        # Use connection pool instead of creating new connection each time
        pool = _get_postgres_pool()
        with pool.connection() as conn:
            yield conn
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


def list_columns(conn: "ConnectionProtocol", table_name: str, use_cache: bool = True) -> Set[str]:
    """Return the existing column names for *table_name*.
    
    Args:
        conn: Database connection
        table_name: Name of the table to inspect
        use_cache: If True, use cached schema info (default). Set to False to force refresh.
    
    Returns:
        Set of column names for the table
    """
    cache_key = f"{USING_POSTGRES}:{table_name}"
    
    # Check cache first if enabled
    if use_cache and cache_key in _schema_cache:
        return _schema_cache[cache_key]

    if USING_POSTGRES:
        cursor = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = current_schema()
            """,
            (table_name,),
        )
        rows = cursor.fetchall()
        columns = {row["column_name"] if isinstance(row, dict) else row[0] for row in rows}
    else:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        # sqlite3.Row can be indexed by name or ordinal
        columns = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in rows}
    
    # Cache the result
    _schema_cache[cache_key] = columns
    return columns


def clear_schema_cache(table_name: Optional[str] = None) -> None:
    """Clear the schema cache for a specific table or all tables.
    
    Args:
        table_name: If provided, clear only this table's cache. Otherwise clear all.
    """
    global _schema_cache
    
    if table_name is None:
        _schema_cache.clear()
    else:
        cache_key = f"{USING_POSTGRES}:{table_name}"
        _schema_cache.pop(cache_key, None)


def execute_batch(conn: "ConnectionProtocol", statements: Sequence[str]) -> None:
    """Execute multiple SQL statements sequentially."""

    for statement in statements:
        conn.execute(statement)


class ConnectionProtocol(sqlite3.Connection):  # type: ignore[misc]
    """Protocol-like class for type checking cross-database connections."""

    # The sqlite3 Connection provides these attributes; for psycopg we rely on duck typing.
    pass


