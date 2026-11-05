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
from rich.table import Table
from rich.panel import Panel

from scraper_agent.config import SCRAPER_CONFIG
from scraper_agent.db.repository import JobRepository
from scraper_agent.discovery.company_finder import (
    DynamicJobDiscovery,
    TARGET_INDUSTRIES,
    normalize_industry_name,
)
from scraper_agent.models.job import Company, JobSource, RawJobPost, ProcessedJob, ScrapeRunStats
from scraper_agent.classifiers.tech_filter import is_technology_job
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location, detect_international_country
from scraper_agent.classifiers.date_filter import (
    is_job_in_date_window,
    get_freshness_cutoff,
    format_freshness_window_description,
)
from scraper_agent.classifiers.jd_analyzer import JDAnalyzer
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.registry import get_scraper_for_type

logger = logging.getLogger(__name__)
console = Console(highlight=False)

DEFAULT_INDUSTRIES = TARGET_INDUSTRIES


class ScraperAgent:
    """
    Scraper Agent executing the exact pipeline:
      1. Start Scraper Agent
      2. Identify Industry
      3. Find Companies in this Industry
      4. In each company, Identify Posted Jobs (Filtered by Date: Prev + Current Month)
      5. Filter Jobs by Technology Nature
      6. Check Job in DB & Classify into Full-Time and Contract
      7. Scrape Job Details (Full JD, Location, Remote Type, Tech Role, Content Hash)
      8. Store Jobs in Database (PostgreSQL)
      9. End
    """

    def __init__(
        self,
        filter_tech_only: Optional[bool] = None,
        enforce_date_window: bool = True,
    ):
        self.repo = JobRepository()
        self.discovery = DynamicJobDiscovery()
        self.filter_tech_only = (
            filter_tech_only
            if filter_tech_only is not None
            else SCRAPER_CONFIG.filter_tech_only
        )
        self.enforce_date_window = enforce_date_window
        self.freshness_cutoff = get_freshness_cutoff()
        self.session_stats = {
            "companies_processed": 0,
            "sources_scraped": 0,
            "jobs_found": 0,
            "fresh_jobs_passed": 0,
            "stale_jobs_skipped": 0,
            "tech_jobs_passed": 0,
            "db_new_jobs": 0,
            "db_existing_jobs": 0,
            "full_time_jobs": 0,
            "contract_jobs": 0,
            "part_time_jobs": 0,
            "internship_jobs": 0,
            "tech_roles_breakdown": {},
            "non_usa_jobs_skipped": 0,
            "new_stored": 0,
            "updated_stored": 0,
            "duplicates_stored": 0,
            "invalid_skipped": 0,
        }

    # Step 1: Start Scraper Agent
    def start(
        self,
        target_industry: Optional[str] = None,
        target_company: Optional[str] = None,
        target_url: Optional[str] = None,
        dynamic_discovery: bool = True,
        target_jobs: int = 0,
        limit_per_industry: int = 0,
    ) -> Dict[str, Any]:
        """Entry point that initializes and executes the complete agent workflow."""
        console.print(
            Panel.fit(
                "[bold cyan]AutoJobApply – Dynamic Scraper Agent (Playwright Career Scraper)[/bold cyan]\n"
                "[dim]Workflow: Identify Industry -> Find Companies -> Identify Posted Jobs (Prev+Current Month) -> "
                "Tech Nature -> Check DB & Classify (Full-Time/Contract) -> Scrape Details -> Store in DB[/dim]",
                border_style="cyan",
            )
        )

        # Handle direct career page URL mode via Playwright
        if target_url:
            console.print(f"[bold green]▶ Direct Career Page Mode (Playwright):[/bold green] [cyan]{target_url}[/cyan]")
            company, source, raw_jobs = self.discovery.scrape_custom_url(
                career_url=target_url, company_name=target_company, industry=target_industry
            )
            console.print(f"  [cyan]Playwright Scraped:[/cyan] Found [bold]{len(raw_jobs)}[/bold] job postings.")
            self._process_single_company_pipeline(company, source, raw_jobs)
            return self.end()

        # Step 2: Identify Industry
        target_industries = self.identify_industry(target_industry)
        console.print(
            f"[dim]🗓 Freshness Window: {format_freshness_window_description()} (Cutoff: {self.freshness_cutoff.strftime('%Y-%m-%d')})[/dim]"
        )

        for industry in target_industries:
            if target_jobs > 0:
                summary = self.repo.get_dashboard_summary()
                if summary["total_jobs"] >= target_jobs:
                    console.print(f"\n[bold green]🎯 Target Goal Reached:[/bold green] {summary['total_jobs']} jobs stored in PostgreSQL!")
                    return self.end()

            console.print(f"\n[bold green]▶ Step 2 (Identify Industry):[/bold green] Target Industry: [bold yellow]{industry}[/bold yellow]")

            # Step 3: Find Companies in Industry
            companies_and_sources = self.find_companies_in_industry(
                industry, company_filter=target_company
            )
            console.print(
                f"[bold green]▶ Step 3 (Find Companies in Industry):[/bold green] Found [bold cyan]{len(companies_and_sources)}[/bold cyan] company(s) with career pages in [yellow]{industry}[/yellow]."
            )

            if not companies_and_sources:
                console.print(f"  [dim]No companies found for industry '{industry}'. Proceeding...[/dim]")
                continue

            active_co_list = companies_and_sources[:limit_per_industry] if limit_per_industry > 0 else companies_and_sources
            for company, source in active_co_list:
                if target_jobs > 0:
                    summary = self.repo.get_dashboard_summary()
                    if summary["total_jobs"] >= target_jobs:
                        console.print(f"\n[bold green]🎯 Target Goal Reached:[/bold green] {summary['total_jobs']} jobs stored in PostgreSQL!")
                        return self.end()
                self._process_company(company, source)

        # Step 9: End
        return self.end()

    # Step 2: Identify Industry
    def identify_industry(self, requested_industry: Optional[str] = None) -> List[str]:
        """
        Determines target industries for job collection.
        If None or 'ALL', returns all 7 target industries:
          1. IT, Software & Technology
          2. Healthcare
          3. Finance & Banking
          4. Insurance
          5. Solar, Energy & Utilities
          6. Aerospace & Defense
          7. Pharma & Biotechnology
        Otherwise normalizes and returns a single-item list with the specified industry.
        """
        if not requested_industry or requested_industry.strip().upper() in ["ALL", ""]:
            return DEFAULT_INDUSTRIES
        normalized = normalize_industry_name(requested_industry)
        if normalized == "ALL":
            return DEFAULT_INDUSTRIES
        return [normalized]

    # Step 3: Find Companies in Industry
    def find_companies_in_industry(
        self, industry: str, company_filter: Optional[str] = None
    ) -> List[Tuple[Company, JobSource]]:
        """
        Flow Step 3: Queries the database and dynamic discovery to find active companies
        operating in the identified industry along with their direct career page sources.
        """
        return self.discovery.find_companies_in_industry(industry, company_filter=company_filter)

    def _process_company(self, company: Company, source: JobSource) -> None:
        """Executes steps 4 through 8 for a company and its career page source."""
        self.session_stats["companies_processed"] += 1
        self.session_stats["sources_scraped"] += 1

        console.print(
            f"\n[bold blue]🏢 Company:[/bold blue] {company.name} [dim]({company.industry or 'General'})[/dim] | [dim]{source.source_url}[/dim]"
        )

        # Step 4: Identify Posted Jobs on Career Page
        console.print(f"  [bold green]▶ Step 4 (Identify Posted Jobs):[/bold green] Scraping career page with Playwright...")
        raw_jobs = self.identify_posted_jobs(source)
        self.session_stats["jobs_found"] += len(raw_jobs)
        console.print(f"  [cyan]Playwright Scraped:[/cyan] Found [bold]{len(raw_jobs)}[/bold] posted jobs on career page.")

        if not raw_jobs:
            console.print(f"  [dim]No active job listings found on {source.source_url}.[/dim]")
            return

        self._process_single_company_pipeline(company, source, raw_jobs)

    def _process_single_company_pipeline(
        self, company: Company, source: JobSource, raw_jobs: List[RawJobPost]
    ) -> None:
        """
        Executes Steps 4 (Date Filter) -> 5 (Tech Nature) -> 6 (Check DB & Classify) -> 7 (Scrape Details) -> 8 (Store in DB).
        """
        run_id = self.repo.start_scrape_run(source.id)
        started_at = datetime.now(timezone.utc)
        stats = ScrapeRunStats(source_id=source.id, started_at=started_at)
        stats.jobs_found = len(raw_jobs)

        try:
            # Step 4 (continued): Date Filter (Previous Month + Current Month)
            fresh_jobs: List[RawJobPost] = []
            stale_count = 0
            for job in raw_jobs:
                if self.enforce_date_window:
                    is_fresh, _ = is_job_in_date_window(job.posted_at, self.freshness_cutoff)
                    if not is_fresh:
                        stale_count += 1
                        continue
                fresh_jobs.append(job)

            self.session_stats["fresh_jobs_passed"] += len(fresh_jobs)
            self.session_stats["stale_jobs_skipped"] += stale_count

            console.print(
                f"  [bold green]🗓 Date Window Filter (Prev + Current Month):[/bold green] "
                f"[bold cyan]{len(fresh_jobs)}[/bold cyan] fresh postings retained"
                + (f" ([dim]{stale_count} older than previous month skipped[/dim])" if stale_count else "")
                + "."
            )

            if not fresh_jobs:
                stats.status = "SUCCESS"
                self.repo.update_job_source_status(source.id, success=True)
                return

            # Step 5: Filter Jobs by Technology Nature
            tech_jobs, non_tech_count = self.filter_jobs_by_technology_nature(fresh_jobs)
            self.session_stats["tech_jobs_passed"] += len(tech_jobs)
            console.print(
                f"  [bold green]▶ Step 5 (Filter by Tech Nature):[/bold green] [cyan]{len(tech_jobs)}[/cyan] tech jobs passed ([dim]{non_tech_count} non-tech filtered out[/dim])."
            )

            if not tech_jobs:
                stats.status = "SUCCESS"
                self.repo.update_job_source_status(source.id, success=True)
                return

            # USA Location Pre-Filter: exclude obvious international jobs early (India, UK, Canada, EMEA, etc.)
            usa_candidates: List[Tuple[RawJobPost, List[str]]] = []
            intl_early_skipped = 0
            for job, kw in tech_jobs:
                raw_loc = job.raw_location or ""
                int_check = detect_international_country(f"{raw_loc} {job.title}")
                if int_check and not any(
                    us_marker in raw_loc.lower()
                    for us_marker in ["united states", "usa", "u.s.", "california", "texas", "new york", "washington"]
                ):
                    intl_early_skipped += 1
                else:
                    usa_candidates.append((job, kw))

            if intl_early_skipped:
                self.session_stats["non_usa_jobs_skipped"] += intl_early_skipped
                console.print(
                    f"  [bold yellow]🇺🇸 USA Pre-Filter:[/bold yellow] Skipped [dim]{intl_early_skipped} overseas/international job(s) (Bengaluru, London, Canada, etc.)[/dim]."
                )

            tech_jobs = usa_candidates
            if not tech_jobs:
                console.print("  [dim]No USA-based tech jobs found for this company.[/dim]")
                stats.status = "SUCCESS"
                self.repo.update_job_source_status(source.id, success=True)
                return

            # Step 6: Check this Job in DB & Classify Employment Type (Full-Time vs Contract)
            job_ids = [j.external_job_id for j, _ in tech_jobs]
            db_existing_map = self.repo.check_existing_jobs(company.id, job_ids)

            new_in_db = sum(1 for jid in job_ids if jid not in db_existing_map)
            existing_in_db = len(job_ids) - new_in_db
            self.session_stats["db_new_jobs"] += new_in_db
            self.session_stats["db_existing_jobs"] += existing_in_db

            # Classify into Full-Time vs Contract branches
            full_time_branch: List[Tuple[RawJobPost, List[str], str]] = []
            contract_branch: List[Tuple[RawJobPost, List[str], str]] = []
            excluded_other_count = 0

            for raw_job, tech_kw in tech_jobs:
                emp_type = JDAnalyzer.deduce_employment_type_from_jd(
                    title=raw_job.title,
                    description=raw_job.raw_description,
                    metadata=raw_job.metadata,
                )
                if emp_type == "FULL_TIME":
                    full_time_branch.append((raw_job, tech_kw, emp_type))
                elif emp_type == "CONTRACT":
                    contract_branch.append((raw_job, tech_kw, emp_type))
                else:
                    # User requirement: ONLY scrape Full-Time and Contract jobs (strictly filter out others)
                    excluded_other_count += 1
                    if emp_type == "PART_TIME":
                        self.session_stats["part_time_jobs"] += 1
                    elif emp_type == "INTERNSHIP":
                        self.session_stats["internship_jobs"] += 1

            console.print(
                f"  [bold green]▶ Step 6 (Check Job in DB & Classify Employment Type):[/bold green]\n"
                f"    ├── [bold magenta]PostgreSQL Status:[/bold magenta] {new_in_db} New Job(s) to Scrape | {existing_in_db} Already in DB\n"
                f"    ├── [bold cyan]Full-Time Jobs Branch:[/bold cyan] {len(full_time_branch)}\n"
                f"    └── [bold yellow]Contract Jobs Branch:[/bold yellow] {len(contract_branch)}"
                + (f" [dim](strictly excluded {excluded_other_count} non-FT/contract: intern/part-time)[/dim]" if excluded_other_count else "")
            )

            # Step 7: Scrape Job Details (Full JD, Tech Role, Location, Content Hash)
            # User requirement: ONLY scrape Full-Time and Contract jobs, NO other
            target_classified = full_time_branch + contract_branch
            processed_jobs: List[ProcessedJob] = []

            console.print(
                f"  [bold green]▶ Step 7 (Scrape Job Details):[/bold green] Fetching full JD descriptions, deducing Tech Roles & attributes for {len(target_classified)} Full-Time & Contract jobs..."
            )

            for raw_job, tech_kw, emp_type in target_classified:
                # Flow Step 7: Always fetch deep job details (full JD, full location, real title) from the job page
                desc = raw_job.raw_description
                if raw_job.job_url and raw_job.job_url.startswith("http"):
                    # Malformed greenhouse /company/ check: immediately reject
                    if "boards.greenhouse.io/company/" in raw_job.job_url:
                        logger.warning(f"Rejecting malformed job URL: {raw_job.job_url}")
                        continue

                    deep_info = BaseScraper.fetch_job_deep_info(raw_job.job_url)

                    # USER REQUIREMENT: Store ONLY active and available URLs (reject 404, 'Sorry, but we can't find that page', expired)
                    if not deep_info.get("is_active", True):
                        logger.warning(f"Skipping inactive/404 job posting: {raw_job.title} ({raw_job.job_url})")
                        continue

                    if deep_info.get("description") and len(deep_info["description"]) > len(desc):
                        desc = deep_info["description"]
                        raw_job.raw_description = desc
                    if deep_info.get("location"):
                        deep_loc = deep_info["location"].strip()
                        # If current location is generic (Remote, Hybrid, empty) or deep location is more detailed
                        if not raw_job.raw_location or raw_job.raw_location.lower() in ["remote", "hybrid", "onsite", "unspecified", "none", ""]:
                            raw_job.raw_location = deep_loc
                        elif any(intl in deep_loc.lower() for intl in ["india", "bengaluru", "hyderabad", "karnataka", "telangana", "pune", "uk", "london", "canada"]):
                            raw_job.raw_location = deep_loc
                    if deep_info.get("title") and (raw_job.title.lower() in ["apply", "apply now", "view job"] or len(raw_job.title) < 5):
                        raw_job.title = deep_info["title"]

                # Deduce Tech Role from Job Description
                tech_role = JDAnalyzer.deduce_tech_role_from_jd(
                    title=raw_job.title, description=desc
                )

                processed_job = self.scrape_job_details(
                    company_id=company.id,
                    source_id=source.id,
                    raw_job=raw_job,
                    employment_type=emp_type,
                    tech_role=tech_role,
                    tech_keywords=tech_kw,
                )
                if processed_job:
                    processed_jobs.append(processed_job)
                    roles_map = self.session_stats["tech_roles_breakdown"]
                    roles_map[tech_role] = roles_map.get(tech_role, 0) + 1
                    # Update session employment counts
                    if emp_type == "FULL_TIME":
                        self.session_stats["full_time_jobs"] += 1
                    elif emp_type == "CONTRACT":
                        self.session_stats["contract_jobs"] += 1
                else:
                    self.session_stats["non_usa_jobs_skipped"] += 1

            # Step 8: Store Jobs in Database
            console.print(
                f"  [bold green]▶ Step 8 (Store Jobs in Database):[/bold green] Storing {len(processed_jobs)} USA jobs in PostgreSQL..."
            )
            if processed_jobs:
                self.store_jobs_in_database(processed_jobs, stats)
                console.print(
                    f"  [bold green]✓ Stored in DB:[/bold green] +{stats.new_jobs} new, ~{stats.updated_jobs} updated, ={stats.duplicate_jobs} existing."
                )
            else:
                console.print("  [dim]No new USA-based jobs to store for this company.[/dim]")

            stats.status = "SUCCESS"
            self.repo.update_job_source_status(source.id, success=True)

        except Exception as exc:
            logger.error(f"Error processing jobs for {company.name} ({source.source_url}): {exc}", exc_info=True)
            stats.status = "FAILED"
            stats.error_message = str(exc)
            self.repo.update_job_source_status(source.id, success=False)
            console.print(f"  [bold red]✗ Failed:[/bold red] {exc}")

        finally:
            stats.completed_at = datetime.now(timezone.utc)
            self.repo.complete_scrape_run(run_id, stats)

    # Step 4: Identify Posted Jobs
    def identify_posted_jobs(self, source: JobSource) -> List[RawJobPost]:
        """Fetches raw job listings from the company's career page using Playwright."""
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
        """Classifies whether the job is 'FULL_TIME' or 'CONTRACT'."""
        return JDAnalyzer.deduce_employment_type_from_jd(
            title=raw_job.title,
            description=raw_job.raw_description,
            metadata=raw_job.metadata,
        )

    # Step 7: Scrape Job Details
    def scrape_job_details(
        self,
        company_id: int,
        source_id: int,
        raw_job: RawJobPost,
        employment_type: str,
        tech_role: str,
        tech_keywords: List[str],
    ) -> Optional[ProcessedJob]:
        """
        Cleans and extracts full job attributes, normalizes geography & remote type,
        assigns deduced tech role, and computes SHA-256 content hash.
        Returns None if job is not confirmed USA-based.
        """
        # Reject malformed or inactive greenhouse URLs
        if not raw_job.job_url or "boards.greenhouse.io/company/" in raw_job.job_url:
            return None

        city, state, country, remote_type = parse_location(
            raw_location=raw_job.raw_location,
            title=raw_job.title,
            description=raw_job.raw_description,
        )

        # STRICT USA-ONLY VALIDATION:
        if not is_usa_location(
            raw_location=raw_job.raw_location,
            title=raw_job.title,
            description=raw_job.raw_description,
            city=city,
            state=state,
            country=country,
        ):
            logger.info(
                f"Skipping non-USA job: {raw_job.title} | {raw_job.raw_location} -> {city}, {state}, {country}"
            )
            return None

        # Confirmed USA location
        country = "United States"

        # Build clean display location: NEVER allow '/ Unspecified' or dummy noise
        clean_display_loc = raw_job.raw_location
        if not clean_display_loc or any(n in clean_display_loc.lower() for n in ["unspecified", "not specified", "n/a", "none"]):
            if city and state:
                clean_display_loc = f"{city}, {state}, United States"
            elif state:
                clean_display_loc = f"{state}, United States"
            elif remote_type == "REMOTE":
                clean_display_loc = "Remote, United States"
            else:
                clean_display_loc = "United States"

        content_hash = BaseScraper.compute_content_hash(
            title=raw_job.title,
            description=raw_job.raw_description,
            location=clean_display_loc,
            employment_type=employment_type,
        )

        return ProcessedJob(
            company_id=company_id,
            source_id=source_id,
            external_job_id=raw_job.external_job_id,
            title=raw_job.title,
            description=raw_job.raw_description,
            location=clean_display_loc,
            city=city,
            state=state,
            country="United States",
            remote_type=remote_type,
            employment_type=employment_type,
            tech_role=tech_role,
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
        table.add_row("Fresh Postings (Prev + Current Month)", str(self.session_stats["fresh_jobs_passed"]))
        table.add_row("Stale Jobs Skipped", str(self.session_stats["stale_jobs_skipped"]))
        table.add_row("Tech Jobs Filtered", str(self.session_stats["tech_jobs_passed"]))
        table.add_row("International (Non-USA) Skipped", str(self.session_stats["non_usa_jobs_skipped"]))
        table.add_row("DB Status Check - New Jobs", str(self.session_stats["db_new_jobs"]))
        table.add_row("DB Status Check - Existing Jobs", str(self.session_stats["db_existing_jobs"]))
        table.add_row("  - Full-Time Jobs", str(self.session_stats["full_time_jobs"]))
        table.add_row("  - Contract Jobs", str(self.session_stats["contract_jobs"]))
        table.add_row("  - Part-Time Jobs", str(self.session_stats["part_time_jobs"]))
        table.add_row("  - Internship Jobs", str(self.session_stats["internship_jobs"]))
        table.add_row("New Jobs Stored in DB", str(self.session_stats["new_stored"]))
        table.add_row("Updated Jobs Stored in DB", str(self.session_stats["updated_stored"]))
        table.add_row("Duplicate / Unchanged Jobs", str(self.session_stats["duplicates_stored"]))
        table.add_row("Invalid Skipped", str(self.session_stats["invalid_skipped"]))

        console.print("\n")
        console.print(table)

        # Print Tech Roles Breakdown Table
        roles_data = self.session_stats.get("tech_roles_breakdown", {})
        if roles_data:
            role_table = Table(title="Top Tech Roles Deduced from JD", border_style="cyan")
            role_table.add_column("Deduced Tech Role", style="yellow")
            role_table.add_column("Count", style="bold green", justify="right")
            for role, cnt in sorted(roles_data.items(), key=lambda x: x[1], reverse=True)[:10]:
                role_table.add_row(role, str(cnt))
            console.print(role_table)

        console.print("[bold green]✔ Scraper Agent Execution Completed.[/bold green]\n")
        return self.session_stats
