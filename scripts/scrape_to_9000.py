"""
High-Yield Multi-ATS Scraper Runner:
Scrapes verified high-yield company career sources across ALL 7 target industries
and ALL ATS platforms (Workday CXS, Greenhouse, Lever, Ashby, SmartRecruiters, Jobvite, Taleo)
until total verified USA jobs stored in PostgreSQL reaches 9,000+.
"""
import sys
import os
import time
from pathlib import Path

# Ensure temporary files stay on D: to prevent disk space exhaustion
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from scraper_agent.db.repository import JobRepository
from scraper_agent.db.schema_manager import initialize_schema
from scraper_agent.db.connection import test_connection
from scraper_agent.agent.scraper_agent import ScraperAgent
from scraper_agent.discovery.company_finder import VERIFIED_INDUSTRY_COMPANIES

console = Console(highlight=False)

TARGET_TOTAL_JOBS = 11000


def run():
    if not test_connection():
        console.print("[bold red]Error: PostgreSQL is not reachable on port 5433.[/bold red]")
        sys.exit(1)

    repo = JobRepository()
    initial_stats = repo.get_dashboard_summary()
    current_jobs = initial_stats["total_jobs"]

    console.print(
        Panel.fit(
            f"[bold cyan]AutoJobApply – Multi-ATS Rapid Scraper to 11,000+ Jobs[/bold cyan]\n"
            f"[yellow]Current Jobs in DB:[/yellow] [bold green]{current_jobs}[/bold green] | "
            f"[yellow]Target Goal:[/yellow] [bold green]{TARGET_TOTAL_JOBS}[/bold green] jobs\n"
            f"[dim]Covering ALL 7 Target Industries across Workday, Greenhouse, Lever, Ashby, SmartRecruiters, Jobvite & Taleo[/dim]",
            border_style="cyan",
        )
    )

    if current_jobs >= TARGET_TOTAL_JOBS:
        console.print(f"[bold green]✔ Target already reached: {current_jobs} jobs in database![/bold green]")
        return

    agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

    # Fetch existing job counts per company to prioritize unscraped and high-yield companies
    existing_job_counts = {}
    from scraper_agent.db.connection import get_db_connection
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT c.name, count(j.id) FROM companies c LEFT JOIN jobs j ON c.id=j.company_id GROUP BY c.name;")
                existing_job_counts = dict(cur.fetchall())
    except Exception as e:
        console.print(f"[yellow]Warning: Could not fetch existing job counts: {e}[/yellow]")

    def get_target_priority(item):
        name, domain, url, industry = item
        count = existing_job_counts.get(name, 0)
        is_unscraped = (count == 0)
        # Direct REST API endpoints execute in < 2 seconds and yield clean full JDs
        if "greenhouse.io" in url:
            tier = 1
        elif "ashbyhq.com" in url:
            tier = 2
        elif "smartrecruiters.com" in url:
            tier = 3
        elif "lever.co" in url:
            tier = 4
        elif "myworkdayjobs.com" in url:
            tier = 5
        else:
            tier = 6
        return (0 if is_unscraped else 1, tier, count)

    raw_targets = []
    for industry, comp_list in VERIFIED_INDUSTRY_COMPANIES.items():
        for c in comp_list:
            url = c["career_url"]
            raw_targets.append((c["name"], c.get("domain", ""), url, industry))

    # Deduplicate raw targets by career URL
    seen_urls = set()
    deduped_targets = []
    for item in raw_targets:
        if item[2] not in seen_urls:
            seen_urls.add(item[2])
            deduped_targets.append(item)

    all_targets = sorted(deduped_targets, key=get_target_priority)

    console.print(f"[bold green]Ready to scrape {len(all_targets)} high-yield multi-ATS company targets...[/bold green]\n")

    pass_num = 1
    while current_jobs < TARGET_TOTAL_JOBS:
        console.print(f"\n[bold magenta]=== Starting Pass {pass_num} towards {TARGET_TOTAL_JOBS} jobs ===[/bold magenta]\n")
        for idx, (name, domain, url, industry) in enumerate(all_targets, 1):
            summary = repo.get_dashboard_summary()
            current_jobs = summary["total_jobs"]

            if current_jobs >= TARGET_TOTAL_JOBS:
                console.print(f"\n[bold green]🎉 SUCCESS! Reached target goal: {current_jobs} jobs stored in PostgreSQL![/bold green]")
                break

            needed = TARGET_TOTAL_JOBS - current_jobs
            console.print(
                f"[bold cyan][{idx}/{len(all_targets)}][/bold cyan] "
                f"Target: [bold yellow]{name}[/bold yellow] ({industry}) | "
                f"DB: [bold green]{current_jobs}[/bold green] / {TARGET_TOTAL_JOBS} ([yellow]{needed} needed[/yellow])"
            )

            company = repo.get_or_create_company(
                name=name, domain=domain, career_url=url, industry=industry
            )
            source = repo.get_or_create_job_source(
                company_id=company.id, source_url=url, scraper_type="playwright"
            )

            try:
                agent._process_company(company, source)
            except Exception as e:
                console.print(f"  [red]Error processing {name}: {e}[/red]")

        pass_num += 1
        summary = repo.get_dashboard_summary()
        current_jobs = summary["total_jobs"]
        if current_jobs >= TARGET_TOTAL_JOBS:
            break

    # Print final summary table
    final_stats = repo.get_dashboard_summary()
    console.print("\n[bold cyan]============= Final Scraping Results =============[/bold cyan]")
    console.print(f"Total Jobs in DB: [bold green]{final_stats['total_jobs']}[/bold green] (Initial: {initial_stats['total_jobs']})")
    console.print(f"Total Companies: [bold green]{final_stats['total_companies']}[/bold green]")
    console.print(f"Active Job Sources: [bold green]{final_stats['active_sources']}[/bold green]\n")

    ind_table = Table(title="Jobs Stored by Industry", border_style="cyan")
    ind_table.add_column("Industry", style="yellow")
    ind_table.add_column("Jobs Count", style="bold green", justify="right")
    for row in final_stats["by_industry"]:
        ind_table.add_row(row["industry"] or "Unclassified", str(row["job_count"]))
    console.print(ind_table)


if __name__ == "__main__":
    run()
