"""
Backfill Vector Embeddings for Existing Jobs in PostgreSQL.

Model: BAAI/bge-base-en-v1.5 (768 dimensions)
Input Text: Combines Title + full Description up to 2,500 characters:
            f"{title}\\n\\n{description}"[:2500]
Destination: jobs.job_embedding (vector(768)) in PostgreSQL
"""
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from scraper_agent.db.connection import get_db_connection, test_connection
from scraper_agent.embeddings.embedder import get_embedder, JobEmbedder

console = Console(highlight=False)

BATCH_SIZE = 64


def backfill_embeddings():
    if not test_connection():
        console.print("[bold red]PostgreSQL connection failed on port 5433![/bold red]")
        sys.exit(1)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM jobs;")
            total_jobs = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM jobs WHERE job_embedding IS NOT NULL;")
            already_embedded = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM jobs WHERE job_embedding IS NULL;")
            needed_embeddings = cur.fetchone()[0]

    console.print(f"[bold cyan]Total Jobs in DB:[/bold cyan] {total_jobs}")
    console.print(f"[bold green]Already Embedded:[/bold green] {already_embedded}")
    console.print(f"[bold yellow]Jobs Needing Embeddings:[/bold yellow] {needed_embeddings}")

    if needed_embeddings == 0:
        console.print("[bold green]✔ All jobs are already vectorized![/bold green]")
        return

    console.print("\n[cyan]Initializing BAAI/bge-base-en-v1.5 model...[/cyan]")
    embedder = get_embedder()
    # Trigger model load
    embedder._ensure_model()
    console.print("[bold green]✔ Model ready.[/bold green]\n")

    t0 = time.time()
    processed_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("• {task.completed}/{task.total} jobs"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Vectorizing jobs...", total=needed_embeddings)

        while True:
            # Fetch a batch of jobs without embeddings
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, title, description 
                        FROM jobs 
                        WHERE job_embedding IS NULL 
                        ORDER BY id ASC 
                        LIMIT %s;
                        """,
                        (BATCH_SIZE,),
                    )
                    rows = cur.fetchall()

            if not rows:
                break

            job_ids = [r[0] for r in rows]
            texts = [embedder.prepare_input_text(r[1], r[2]) for r in rows]

            # Compute embeddings
            embeddings = embedder.embed_texts(texts, batch_size=BATCH_SIZE)

            # Prepare update data: list of (pg_str, job_id)
            update_data = [
                (embedder.vector_to_pg_string(vec), jid)
                for vec, jid in zip(embeddings, job_ids)
            ]

            # Update PostgreSQL in a single transaction
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        UPDATE jobs 
                        SET job_embedding = %s::vector 
                        WHERE id = %s;
                        """,
                        update_data,
                    )

            processed_count += len(rows)
            progress.update(task, advance=len(rows))

    elapsed = time.time() - t0
    console.print(f"\n[bold green]✔ Successfully vectorized and stored {processed_count} jobs in {elapsed:.1f}s ({processed_count / elapsed:.1f} jobs/s)![/bold green]")

    # Verify counts
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM jobs WHERE job_embedding IS NOT NULL;")
            final_embedded = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM jobs WHERE job_embedding IS NULL;")
            remaining_null = cur.fetchone()[0]

    console.print(f"[bold cyan]Final Status:[/bold cyan] {final_embedded} jobs with 768-dim embeddings, {remaining_null} null.\n")


if __name__ == "__main__":
    backfill_embeddings()
