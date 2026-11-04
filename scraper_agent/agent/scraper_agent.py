import logging
import sys
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scraper_agent.config import SCRAPER_CONFIG
from scraper_agent.db.repository import JobRepository
from scraper_agent.models.job import (
    Company,
    JobSource,
    RawJobPost,
    ProcessedJob,
    ScrapeRunStats,
)
from scraper_agent.scrapers.registry import get_scraper_for_type
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.classifiers.tech_filter import is_technology_job
from scraper_agent.classifiers.employment import classify_employment_type
from scraper_agent.classifiers.location_parser import parse_location

logger = logging.getLogger(__name__)
console = Console(highlight=False)


class ScraperAgent:
    """
    Main Orchestrator Agent executing the pipeline specified in the flow diagram:
    
    1. Start Scraper Agent
    2. Identify Industry
    3. Find Companies in Industry
    4. Identify Posted Jobs
    5. Filter Jobs by Technology Nature
    6. Classify Employment Type (Full-Time vs Contract)
    7. Scrape Job Details
    8. Store Jobs in Database
    9. End
    """

    def __init__(self, filter_tech_only: Optional[bool] = None):
        self.repo = JobRepository()
        self.filter_tech_only = (
            filter_tech_only
            if filter_tech_only is not None
            else SCRAPER_CONFIG.filter_tech_only
        )
        self.session_stats = {
            "companies_processed": 0,
            "sources_scraped": 0,
            "jobs_found": 0,
            "tech_jobs_passed": 0,
            "full_time_jobs": 0,
            "contract_jobs": 0,
            "new_stored": 0,
            "updated_stored": 0,
            "duplicates_stored": 0,
            "invalid_skipped": 0,
        }

    # Step 1: Start Scraper Agent
    def start(self, target_industry: Optional[str] = None, target_company: Optional[str] = None) -> Dict[str, Any]:
        """Entry point that initializes and executes the complete agent workflow."""
        console.print(
            Panel.fit(
                "[bold cyan]AutoJobApply – Scraper Agent[/bold cyan]\n"
                "[dim]Workflow Execution: Industry -> Companies -> Posted Jobs -> Tech Filter -> Employment Classification -> Details Scrape -> Database Storage[/dim]",
                border_style="cyan",
            )
        )

        # Step 2: Identify Industry
        industry = self.identify_industry(target_industry)
        console.print(f"[bold green]▶ Step 1 & 2:[/bold green] Agent started for industry: [yellow]{industry}[/yellow]")

        # Step 3: Find Companies in Industry
        companies = self.find_companies_in_industry(industry, company_filter=target_company)
        if not companies:
            console.print(f"[yellow]No active companies found for industry '{industry}'.[/yellow]")
            return self.end()

        console.print(
            f"[bold green]▶ Step 3:[/bold green] Found [cyan]{len(companies)}[/cyan] company(s) in [yellow]{industry}[/yellow]."
        )

        # Process each company and its sources
        for comp in companies:
            self._process_company(comp)

        # Step 9: End
        return self.end()

    # Step 2: Identify Industry
    def identify_industry(self, requested_industry: Optional[str] = None) -> str:
        """
        Determines the target industry for job collection.
        If None or 'ALL', processes all available industries.
        """
        if requested_industry and requested_industry.strip():
            return requested_industry.strip()
        return "ALL"

    # Step 3: Find Companies in Industry
    def find_companies_in_industry(
        self, industry: str, company_filter: Optional[str] = None
    ) -> List[Company]:
        """Queries the database for active companies matching the target industry."""
        if company_filter:
            company = self.repo.get_company_by_name(company_filter)
            return [company] if company else []
        return self.repo.get_companies_by_industry(industry)

    def _process_company(self, company: Company) -> None:
        """Processes all active job sources for a single company."""
        sources = self.repo.get_active_sources_for_company(company.id)
        if not sources:
            console.print(f"  [dim]No active job sources for {company.name}. Skipping.[/dim]")
            return

        self.session_stats["companies_processed"] += 1
        console.print(f"\n[bold blue]🏢 Company:[/bold blue] {company.name} [dim]({company.industry or 'General'})[/dim]")

        for source in sources:
            self._process_source(company, source)

    def _process_source(self, company: Company, source: JobSource) -> None:
        """Executes steps 4 through 8 for a given job source."""
        self.session_stats["sources_scraped"] += 1
        run_id = self.repo.start_scrape_run(source.id)
        started_at = datetime.now(timezone.utc)
        stats = ScrapeRunStats(source_id=source.id, started_at=started_at)

        try:
            # Step 4: Identify Posted Jobs
            raw_jobs = self.identify_posted_jobs(source)
            stats.jobs_found = len(raw_jobs)
            self.session_stats["jobs_found"] += len(raw_jobs)
            console.print(
                f"  [cyan]Source ({source.scraper_type}):[/cyan] Found [bold]{len(raw_jobs)}[/bold] posted jobs."
            )

            # Step 5: Filter Jobs by Technology Nature
            tech_jobs, non_tech_count = self.filter_jobs_by_technology_nature(raw_jobs)
            self.session_stats["tech_jobs_passed"] += len(tech_jobs)
            console.print(
                f"  [magenta]Tech Filter:[/magenta] Retained [bold green]{len(tech_jobs)}[/bold green] tech jobs ([dim]{non_tech_count} non-tech filtered out[/dim])."
            )

            # Step 6 & 7: Classify Employment Type & Scrape Job Details
            processed_jobs: List[ProcessedJob] = []
            for raw_job, tech_kw in tech_jobs:
                # Step 6: Classify Employment Type (Full-Time vs Contract)
                emp_type = self.classify_employment_type(raw_job)
                if emp_type == "CONTRACT":
                    self.session_stats["contract_jobs"] += 1
                else:
                    self.session_stats["full_time_jobs"] += 1

                # Step 7: Scrape Job Details
                processed_job = self.scrape_job_details(
                    company_id=company.id,
                    source_id=source.id,
                    raw_job=raw_job,
                    employment_type=emp_type,
                    tech_keywords=tech_kw,
                )
                processed_jobs.append(processed_job)

            # Step 8: Store Jobs in Database
            self.store_jobs_in_database(processed_jobs, stats)

            stats.status = "SUCCESS"
            self.repo.update_job_source_status(source.id, success=True)
            console.print(
                f"  [bold green]✓ Stored in DB:[/bold green] +{stats.new_jobs} new, ~{stats.updated_jobs} updated, ={stats.duplicate_jobs} existing."
            )

        except Exception as exc:
            logger.error(f"Error scraping source {source.id} ({source.source_url}): {exc}", exc_info=True)
            stats.status = "FAILED"
            stats.error_message = str(exc)
            self.repo.update_job_source_status(source.id, success=False)
            console.print(f"  [bold red]✗ Failed:[/bold red] {exc}")

        finally:
            stats.completed_at = datetime.now(timezone.utc)
            self.repo.complete_scrape_run(run_id, stats)

    # Step 4: Identify Posted Jobs
    def identify_posted_jobs(self, source: JobSource) -> List[RawJobPost]:
        """Fetches raw job listings from the company's job source using appropriate scraper."""
        scraper = get_scraper_for_type(source.scraper_type)
        return scraper.fetch_jobs(source.source_url)

    # Step 5: Filter Jobs by Technology Nature
    def filter_jobs_by_technology_nature(
        self, raw_jobs: List[RawJobPost]
    ) -> Tuple[List[Tuple[RawJobPost, List[str]]], int]:
        """
        Filters raw jobs based on technology/software engineering keywords.
        Returns (list_of_accepted_jobs_with_matched_keywords, filtered_out_count).
        """
        if not self.filter_tech_only:
            # If tech filter disabled, pass all jobs
            return [(j, ["all"]) for j in raw_jobs], 0

        accepted: List[Tuple[RawJobPost, List[str]]] = []
        filtered_out = 0

        for job in raw_jobs:
            is_tech, keywords = is_technology_job(
                title=job.title, description=job.raw_description
            )
            if is_tech:
                accepted.append((job, keywords))
            else:
                filtered_out += 1

        return accepted, filtered_out

    # Step 6: Classify Employment Type
    def classify_employment_type(self, raw_job: RawJobPost) -> str:
        """
        Classifies whether the job is 'FULL_TIME' or 'CONTRACT'.
        """
        return classify_employment_type(
            title=raw_job.title,
            description=raw_job.raw_description,
            source_metadata=raw_job.metadata,
        )

    # Step 7: Scrape Job Details
    def scrape_job_details(
        self,
        company_id: int,
        source_id: int,
        raw_job: RawJobPost,
        employment_type: str,
        tech_keywords: List[str],
    ) -> ProcessedJob:
        """
        Cleans and extracts full job attributes, normalizes geography & remote type,
        and computes SHA-256 content hash.
        """
        city, state, country, remote_type = parse_location(
            raw_location=raw_job.raw_location,
            title=raw_job.title,
            description=raw_job.raw_description,
        )

        content_hash = BaseScraper.compute_content_hash(
            title=raw_job.title,
            description=raw_job.raw_description,
            location=raw_job.raw_location,
            employment_type=employment_type,
        )

        return ProcessedJob(
            company_id=company_id,
            source_id=source_id,
            external_job_id=raw_job.external_job_id,
            title=raw_job.title,
            description=raw_job.raw_description,
            location=raw_job.raw_location,
            city=city,
            state=state,
            country=country,
            remote_type=remote_type,
            employment_type=employment_type,
            posted_at=raw_job.posted_at,
            source_updated_at=raw_job.source_updated_at,
            job_url=raw_job.job_url,
            application_url=raw_job.application_url or raw_job.job_url,
            content_hash=content_hash,
            is_tech=True,
            tech_keywords=tech_keywords,
            status="OPEN",
        )

    # Step 8: Store Jobs in Database
    def store_jobs_in_database(
        self, jobs: List[ProcessedJob], stats: ScrapeRunStats
    ) -> None:
        """Persists processed jobs to the PostgreSQL jobs table with deduplication and tracking."""
        new_cnt, updated_cnt, duplicate_cnt, invalid_cnt = self.repo.upsert_jobs_batch(jobs)
        stats.new_jobs += new_cnt
        stats.updated_jobs += updated_cnt
        stats.duplicate_jobs += duplicate_cnt
        stats.invalid_jobs += invalid_cnt

        self.session_stats["new_stored"] += new_cnt
        self.session_stats["updated_stored"] += updated_cnt
        self.session_stats["duplicates_stored"] += duplicate_cnt
        self.session_stats["invalid_skipped"] += invalid_cnt

    # Step 9: End
    def end(self) -> Dict[str, Any]:
        """Wraps up execution and prints final session summary table."""
        table = Table(title="Scraper Agent Execution Summary", border_style="green")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Count", style="bold yellow")

        table.add_row("Companies Processed", str(self.session_stats["companies_processed"]))
        table.add_row("Sources Scraped", str(self.session_stats["sources_scraped"]))
        table.add_row("Total Raw Jobs Found", str(self.session_stats["jobs_found"]))
        table.add_row("Tech Jobs Filtered", str(self.session_stats["tech_jobs_passed"]))
        table.add_row("  - Full-Time Jobs", str(self.session_stats["full_time_jobs"]))
        table.add_row("  - Contract Jobs", str(self.session_stats["contract_jobs"]))
        table.add_row("New Jobs Stored", str(self.session_stats["new_stored"]))
        table.add_row("Updated Jobs Stored", str(self.session_stats["updated_stored"]))
        table.add_row("Duplicate / Unchanged Jobs", str(self.session_stats["duplicates_stored"]))
        table.add_row("Invalid Skipped", str(self.session_stats["invalid_skipped"]))

        console.print("\n")
        console.print(table)
        console.print("[bold green]✔ Scraper Agent Execution Completed.[/bold green]\n")
        return self.session_stats
