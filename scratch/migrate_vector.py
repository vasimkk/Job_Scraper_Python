import sys
sys.path.insert(0, ".")
from scraper_agent.db.connection import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        print("Ensuring pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("Adding job_embedding vector(768) to jobs table...")
        cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_embedding vector(768);")
        print("Creating HNSW index on jobs(job_embedding)...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_embedding ON jobs USING hnsw (job_embedding vector_cosine_ops);")
        conn.commit()
        
        # Verify columns in jobs
        cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'job_embedding';")
        row = cur.fetchone()
        print("job_embedding column verified:", row)
print("Migration completed successfully!")

