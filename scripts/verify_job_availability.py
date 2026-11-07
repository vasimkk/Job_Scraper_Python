"""
Job Availability Verification Tool
Strictly enforces the Important Database Rules:
  - URL Active + Job Open: Keep job Active.
  - URL Active + Job Closed: Mark job Closed.
  - URL Active + Status Unclear: Keep existing status; do not mark Closed.
  - URL Inaccessible: Retry verification before changing status.
  - CAPTCHA/Login/Network Error: Do not change job status.
  - Confirmed Closed: Update the database to Closed.
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from scraper_agent.db.connection import test_connection
from scraper_agent.verification.verifier import JobBatchVerifier

console = Console(highlight=False)


def main():
    parser = argparse.ArgumentParser(
        description="Verify Job Availability adhering to the Important Database Rules"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of jobs to verify (0 = all jobs in database)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent worker threads (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run verification without writing changes to the database",
    )
    parser.add_argument(
        "--status",
        type=str,
        default="OPEN",
        help="Target job status to verify in database (default: 'OPEN', or 'ALL')",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]=======================================================[/bold cyan]")
    console.print("[bold cyan]       Job Availability Verification (Database Rules)   [/bold cyan]")
    console.print("[bold cyan]=======================================================[/bold cyan]")

    if not test_connection():
        console.print(
            "[bold red]Error:[/bold red] Cannot connect to PostgreSQL database. Please ensure PostgreSQL is running."
        )
        sys.exit(1)

    verifier = JobBatchVerifier(max_workers=args.workers)
    verifier.run_verification(
        limit=args.limit if args.limit > 0 else None,
        dry_run=args.dry_run,
        status_filter=args.status,
    )


if __name__ == "__main__":
    main()

