"""
Batch Scraper Runner:
Scrapes across the 7 Target Industries to populate 1,000+ real tech jobs
(Full-Time and Contract only) into the PostgreSQL database.
"""
import sys
import os
from pathlib import Path

# Set temp directory on D: to prevent disk space issues
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from scraper_agent.db.repository import JobRepository
from scraper_agent.discovery.company_finder import DynamicJobDiscovery, TARGET_INDUSTRIES
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)


def run_batch_scrape(target_total_jobs: int = 1000):
    repo = JobRepository()
    discovery = DynamicJobDiscovery(headless=True)
    agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

    summary = repo.get_dashboard_summary()
    current_jobs = summary["total_jobs"]
    console.print(f"[bold cyan]Starting Multi-Industry Batch Scraper...[/bold cyan]")
    console.print(f"Current Jobs in PostgreSQL: [bold green]{current_jobs}[/bold green] | Target: [bold yellow]{target_total_jobs}[/bold yellow]")

    if current_jobs >= target_total_jobs:
        console.print(f"[bold green]✔ Target of {target_total_jobs} jobs already reached in database![/bold green]")
        return

    # Iterate through all 7 industries
    for industry in TARGET_INDUSTRIES:
        summary = repo.get_dashboard_summary()
        if summary["total_jobs"] >= target_total_jobs:
            console.print(f"\n[bold green]🎯 Target Goal Reached:[/bold green] {summary['total_jobs']} jobs stored in PostgreSQL!")
            break

        console.print(f"\n[bold yellow]═══════════════════════════════════════════════════════[/bold yellow]")
        console.print(f"[bold yellow]▶ Processing Industry: {industry}[/bold yellow]")
        console.print(f"[bold yellow]═══════════════════════════════════════════════════════[/bold yellow]")

        companies_and_sources = discovery.find_companies_in_industry(industry)
        console.print(f"  Found {len(companies_and_sources)} registered companies in {industry}.")

        # Scrape top companies in each industry
        for company, source in companies_and_sources[:15]:
            summary = repo.get_dashboard_summary()
            if summary["total_jobs"] >= target_total_jobs:
                console.print(f"\n[bold green]🎯 Target Goal Reached:[/bold green] {summary['total_jobs']} jobs stored in PostgreSQL!")
                return

            console.print(f"\n🏢 [{industry}] Scraping {company.name} ({source.source_url})...")
            try:
                agent._process_company(company, source)
            except Exception as e:
                console.print(f"  [dim]Skipping {company.name} due to: {e}[/dim]")
                continue

    final_summary = repo.get_dashboard_summary()
    console.print(f"\n[bold green]✔ Batch Scrape Complete! Total Jobs in DB: {final_summary['total_jobs']}[/bold green]")


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run_batch_scrape(target)

