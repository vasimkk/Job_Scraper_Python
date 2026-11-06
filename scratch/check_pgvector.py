import sys
sys.path.insert(0, ".")
from scraper_agent.db.connection import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        print("PG version:", cur.fetchone()[0])
        cur.execute("SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'vector';")
        row = cur.fetchone()
        print("Vector extension available:", row)
        if row:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            print("Successfully created / ensured extension vector!")
            cur.execute("SELECT typname FROM pg_type WHERE typname = 'vector';")
            print("Vector type in DB:", cur.fetchall())
        else:
            print("Vector extension not in pg_available_extensions.")

