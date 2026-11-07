import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from scraper_agent.db.repository import JobRepository
from scraper_agent.verification.checker import JobAvailabilityChecker
from scraper_agent.verification.models import (
    VerificationAction,
    VerificationReason,
    JobVerificationResult,
)

logger = logging.getLogger(__name__)
console = Console(highlight=False)


class JobBatchVerifier:
    """
    Coordinates batch verification across database jobs strictly enforcing the Important Database Rules:
      - URL Active + Job Open: Keep job Active.
      - URL Active + Job Closed: Mark job Closed.
      - URL Active + Status Unclear: Keep existing status; do not mark Closed.
      - URL Inaccessible: Retry verification before changing status.
      - CAPTCHA/Login/Network Error: Do not change job status.
      - Confirmed Closed: Update the database to Closed.
    """

    def __init__(
        self,
        checker: Optional[JobAvailabilityChecker] = None,
        repo: Optional[JobRepository] = None,
        max_workers: int = 10,
    ):
        self.checker = checker or JobAvailabilityChecker()
        self.repo = repo or JobRepository()
        self.max_workers = max_workers

    def verify_single_job(self, job_dict: Dict[str, Any]) -> JobVerificationResult:
        """Runs the 6 rules against a single job database dictionary."""
        return self.checker.verify_job(
            job_url=job_dict.get("job_url", ""),
            job_id=job_dict.get("id", 0),
            title=job_dict.get("title"),
            company_name=job_dict.get("company_name"),
            external_job_id=job_dict.get("external_job_id"),
        )

    def run_verification(
        self,
        limit: Optional[int] = None,
        dry_run: bool = False,
        status_filter: str = "OPEN",
    ) -> Dict[str, Any]:
        """
        Runs batch availability verification on jobs in PostgreSQL.
        Applies database status changes ONLY when confirmed closed or active.
        Preserves existing status on unclear results or errors.
        """
        console.print("\n[bold cyan]═══ Starting Job Availability Verification ═══[/bold cyan]")
        console.print(f"Workers: [green]{self.max_workers}[/green] | Target: [green]{status_filter}[/green] | Dry Run: [dim]{dry_run}[/dim]\n")

        # Fetch jobs to verify
        jobs_to_check = self.get_jobs_for_check(limit=limit, status=status_filter)
        total_jobs = len(jobs_to_check)
        if total_jobs == 0:
            console.print("[yellow]No jobs found matching verification criteria.[/yellow]\n")
            return {"total": 0, "active": 0, "closed": 0, "unclear": 0, "no_change": 0}

        console.print(f"Found [bold green]{total_jobs}[/bold green] jobs to verify in database.\n")

        results: List[JobVerificationResult] = []
        action_counts = {
            VerificationAction.KEEP_ACTIVE.value: 0,
            VerificationAction.MARK_CLOSED.value: 0,
            VerificationAction.KEEP_STATUS.value: 0,
            VerificationAction.NO_CHANGE.value: 0,
        }

        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Verifying Job Rules...", total=total_jobs)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_job = {
                    executor.submit(self.verify_single_job, job): job
                    for job in jobs_to_check
                }

                for future in as_completed(future_to_job):
                    res = future.result()
                    results.append(res)
                    action_counts[res.action.value] += 1
                    progress.advance(task)

        elapsed = round(time.time() - start_time, 2)

        # Database Update Step according to rules
        updated_db_counts = {"CLOSED": 0, "OPEN": 0, "UNTOUCHED": 0}

        if not dry_run:
            console.print("\n[cyan]Applying Database Rules...[/cyan]")
            from scraper_agent.db.connection import get_db_connection

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    for res in results:
                        if res.action == VerificationAction.MARK_CLOSED:
                            # Confirmed Closed: Update the database to Closed
                            cur.execute(
                                """
                                UPDATE jobs
                                SET status = 'CLOSED',
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                                """,
                                (res.job_id,),
                            )
                            updated_db_counts["CLOSED"] += 1

                        elif res.action == VerificationAction.KEEP_ACTIVE:
                            # URL Active + Job Open: Keep job Active
                            cur.execute(
                                """
                                UPDATE jobs
                                SET status = 'OPEN',
                                    last_seen_at = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                                """,
                                (res.job_id,),
                            )
                            updated_db_counts["OPEN"] += 1

                        else:
                            # URL Active + Status Unclear: Keep existing status; do not mark Closed
                            # CAPTCHA/Login/Network Error: Do not change job status
                            updated_db_counts["UNTOUCHED"] += 1

        # Summary Display
        self._print_summary(
            total=total_jobs,
            counts=action_counts,
            updated_db_counts=updated_db_counts,
            elapsed_seconds=elapsed,
            results=results,
        )

        return {
            "total": total_jobs,
            "active": action_counts[VerificationAction.KEEP_ACTIVE.value],
            "closed": action_counts[VerificationAction.MARK_CLOSED.value],
            "unclear": action_counts[VerificationAction.KEEP_STATUS.value],
            "no_change": action_counts[VerificationAction.NO_CHANGE.value],
            "updated_db_counts": updated_db_counts,
            "elapsed_seconds": elapsed,
        }

    def get_jobs_for_check(
        self,
        limit: Optional[int] = None,
        status: str = "OPEN",
    ) -> List[Dict[str, Any]]:
        """Retrieves jobs from PostgreSQL to be audited."""
        from scraper_agent.db.connection import get_dict_cursor
        with get_dict_cursor() as cur:
            query = """
                SELECT j.id, j.company_id, c.name as company_name, j.title, j.job_url,
                       j.application_url, j.external_job_id, j.status, j.first_seen_at, j.last_seen_at
                FROM jobs j
                LEFT JOIN companies c ON c.id = j.company_id
            """
            params: List[Any] = []
            if status and status.upper() != "ALL":
                query += " WHERE j.status = %s"
                params.append(status.upper())

            query += " ORDER BY j.last_seen_at ASC, j.id ASC"

            if limit and limit > 0:
                query += " LIMIT %s"
                params.append(limit)

            cur.execute(query, tuple(params))
            return cur.fetchall()

    @staticmethod
    def _print_summary(
        total: int,
        counts: Dict[str, int],
        updated_db_counts: Dict[str, int],
        elapsed_seconds: float,
        results: List[JobVerificationResult],
    ) -> None:
        """Prints a rich formatted table matching the Important Database Rules."""
        table = Table(title="Database Rules Execution Summary", border_style="cyan")
        table.add_column("Rule / Condition", style="yellow")
        table.add_column("Jobs Evaluated", style="bold green", justify="right")
        table.add_column("Database Action Taken", style="magenta")

        table.add_row(
            "URL Active + Job Open",
            str(counts[VerificationAction.KEEP_ACTIVE.value]),
            "Keep job Active (status = OPEN maintained)",
        )
        table.add_row(
            "URL Active + Job Closed (Confirmed)",
            str(counts[VerificationAction.MARK_CLOSED.value]),
            "Mark job Closed (status = CLOSED updated)",
        )
        table.add_row(
            "URL Active + Status Unclear",
            str(counts[VerificationAction.KEEP_STATUS.value]),
            "[bold green]Kept existing status; NOT marked closed[/bold green]",
        )
        table.add_row(
            "CAPTCHA / Login / Network Error",
            str(counts[VerificationAction.NO_CHANGE.value]),
            "[bold green]Do not change job status (untouched)[/bold green]",
        )
        table.add_row(
            "Total Jobs Processed",
            str(total),
            f"Updated in DB: {updated_db_counts['CLOSED']} Closed | {updated_db_counts['OPEN']} Active Refreshed",
        )
        table.add_row(
            "Execution Time",
            f"{elapsed_seconds:.1f}s",
            f"~{total / max(elapsed_seconds, 0.01):.1f} jobs/sec",
        )
        console.print(table)

        # Print sample closed jobs if any
        closed_samples = [r for r in results if r.action == VerificationAction.MARK_CLOSED][:5]
        if closed_samples:
            ct = Table(title="Sample Confirmed Closed Jobs", border_style="red")
            ct.add_column("ID", style="dim")
            ct.add_column("Company / Title", style="cyan")
            ct.add_column("Reason", style="yellow")
            for cs in closed_samples:
                disp = f"{cs.company_name or 'Company'} - {cs.title or 'Job'}"
                ct.add_row(str(cs.job_id), disp[:45], cs.details.notes[:60])
            console.print(ct)
        console.print()

