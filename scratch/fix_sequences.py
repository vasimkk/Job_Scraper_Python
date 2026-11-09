import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper_agent.db.connection import get_db_connection

tables = ["companies", "job_sources", "jobs", "scrape_runs"]

with get_db_connection() as conn:
    with conn.cursor() as cur:
        for t in tables:
            cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {t}")
            max_id = cur.fetchone()[0]
            
            # Find the sequence name for the table's id column
            cur.execute(f"SELECT pg_get_serial_sequence('{t}', 'id')")
            seq_res = cur.fetchone()
            seq_name = seq_res[0] if seq_res else None
            
            print(f"Table: {t}, max(id): {max_id}, sequence: {seq_name}")
            
            if seq_name:
                # Sync sequence: setval to max_id (if max_id > 0) or 1 with is_called = false
                if max_id > 0:
                    cur.execute(f"SELECT setval('{seq_name}', {max_id}, true)")
                    print(f"  -> Reset {seq_name} to {max_id} (true)")
                else:
                    cur.execute(f"SELECT setval('{seq_name}', 1, false)")
                    print(f"  -> Reset {seq_name} to 1 (false)")

print("Sequence sync completed!")
