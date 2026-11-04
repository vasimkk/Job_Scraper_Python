import logging
from contextlib import contextmanager
from typing import Generator
import psycopg
from psycopg.rows import dict_row

from scraper_agent.config import DB_CONFIG

logger = logging.getLogger(__name__)


def test_connection() -> bool:
    """Test PostgreSQL connectivity using the configured credentials."""
    try:
        with psycopg.connect(DB_CONFIG.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception as exc:
        logger.error(
            f"Failed to connect to PostgreSQL at {DB_CONFIG.host}:{DB_CONFIG.port}/{DB_CONFIG.name}: {exc}"
        )
        return False


@contextmanager
def get_db_connection(row_factory=None) -> Generator[psycopg.Connection, None, None]:
    """
    Context manager yielding a database connection.
    Automatically commits on normal exit and rolls back on exception.
    """
    conn = psycopg.connect(DB_CONFIG.connection_string, row_factory=row_factory)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_dict_cursor():
    """Context manager yielding a cursor that returns rows as dictionaries."""
    with get_db_connection(row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            yield cur

