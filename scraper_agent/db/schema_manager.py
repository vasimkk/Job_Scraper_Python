import logging
from pathlib import Path
from scraper_agent.db.connection import get_db_connection

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"


def initialize_schema() -> None:
    """Reads and executes schema.sql to ensure all required tables, constraints, and indexes exist."""
    schema_file = SQL_DIR / "schema.sql"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_file}")

    sql_content = schema_file.read_text(encoding="utf-8")
    logger.info("Applying database schema...")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_content)
            # Ensure industry column exists on companies in case table pre-existed
            cur.execute(
                "ALTER TABLE companies ADD COLUMN IF NOT EXISTS industry VARCHAR(100);"
            )
            # Ensure tech_role column exists on jobs
            cur.execute(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tech_role VARCHAR(100);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_tech_role ON jobs(tech_role);"
            )

    logger.info("Database schema initialized successfully.")


def seed_database() -> None:
    """Reads and executes seed_data.sql to populate initial companies and ATS job sources."""
    seed_file = SQL_DIR / "seed_data.sql"
    if not seed_file.exists():
        raise FileNotFoundError(f"Seed file not found at: {seed_file}")

    sql_content = seed_file.read_text(encoding="utf-8")
    logger.info("Applying seed companies and job sources...")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_content)

    logger.info("Database seeded successfully with companies and job sources.")

