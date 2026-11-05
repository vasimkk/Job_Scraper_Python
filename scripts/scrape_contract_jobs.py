"""
Targeted Contract Job Scraper:
Specifically scrapes and stores contract-based technology jobs into PostgreSQL.
"""
import sys
import os
from pathlib import Path

os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.table import Table

from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)

CONTRACT_HEAVY_SOURCES = [
    # Company Name, Career Board URL, Industry
    ("Tech Holding", "https://boards.greenhouse.io/techholding", "IT, Software & Technology"),
    ("Upstart", "https://boards.greenhouse.io/upstart", "Finance & Banking"),
    ("Civis Analytics", "https://boards.greenhouse.io/civisanalytics", "IT, Software & Technology"),
    ("Two Six Technologies", "https://boards.greenhouse.io/twosixtechnologies", "Aerospace & Defense"),
    ("Nava PBC", "https://boards.greenhouse.io/navapbc", "IT, Software & Technology"),
    ("Rocket Lab", "https://boards.greenhouse.io/rocketlab", "Aerospace & Defense"),
    ("Komodo Health", "https://boards.greenhouse.io/komodohealth", "Healthcare"),
    ("Astranis", "https://boards.greenhouse.io/astranis", "Aerospace & Defense"),
]


def run_contract_scrape():
    repo = JobRepository()
    agent = ScraperAgent(filter_tech_only=True, enforce_date_window=False)

    console.print("\n[bold cyan]================================================================[/bold cyan]")
    console.print("[bold cyan]▶ Starting Targeted Contract Job Scraper Pipeline...[/bold cyan]")
    console.print("[bold cyan]================================================================[/bold cyan]\n")

    for comp_name, board_url, industry in CONTRACT_HEAVY_SOURCES:
        console.print(f"\n[bold green]Scraping source:[/bold green] {comp_name} ({industry}) -> [cyan]{board_url}[/cyan]")
        try:
            company = repo.get_or_create_company(
                name=comp_name,
                domain=board_url.split("/")[-1] + ".com",
                career_url=board_url,
                industry=industry,
            )
            source = repo.get_or_create_job_source(
                company_id=company.id,
                source_url=board_url,
                scraper_type="playwright",
            )
            raw_jobs = agent.identify_posted_jobs(source)
            console.print(f"  Found {len(raw_jobs)} listings on board.")
            if raw_jobs:
                agent._process_single_company_pipeline(company, source, raw_jobs)
        except Exception as e:
            console.print(f"  [bold red]Error scraping {comp_name}:[/bold red] {e}")

    summary = repo.get_dashboard_summary()
    console.print("\n[bold green]✔ Contract Scrape Finished![/bold green]")
    console.print(f"Total Jobs in DB: [bold green]{summary['total_jobs']}[/bold green]")
    for r in summary["by_employment_type"]:
        console.print(f"  - {r['emp_type']}: [bold yellow]{r['count']}[/bold yellow]")


if __name__ == "__main__":
    run_contract_scrape()
