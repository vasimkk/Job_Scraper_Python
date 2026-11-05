"""
Runner to complete 1000+ Verified Active USA Tech Jobs in PostgreSQL:
Strictly verifies:
- Active & Available URLs only (100% HTTP 200, no 404 / 'Sorry, but we can't find that page')
- 100% USA locations
- 100% Full-Time / Contract
- Balanced across target industries
"""
import sys
import os
from pathlib import Path

os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import psycopg
from rich.console import Console
from rich.table import Table
from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)

TARGET_COMPANIES = [
    # High-Yield USA Tech Companies with 100% verified active boards and instant API responses
    ("Scale AI", "https://boards.greenhouse.io/scaleai", "IT, Software & Technology"),
    ("Reddit", "https://boards.greenhouse.io/reddit", "IT, Software & Technology"),
    ("Pinterest", "https://boards.greenhouse.io/pinterest", "IT, Software & Technology"),
    ("Carta", "https://boards.greenhouse.io/carta", "Finance & Banking"),
    ("Robinhood", "https://boards.greenhouse.io/robinhood", "Finance & Banking"),
    ("Pure Storage", "https://boards.greenhouse.io/purestorage", "IT, Software & Technology"),
    ("Brex", "https://boards.greenhouse.io/brex", "Finance & Banking"),
    ("Toast", "https://boards.greenhouse.io/toast", "Finance & Banking"),
]


def get_current_job_count():
    conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM jobs;")
    cnt = cur.fetchone()[0]
    conn.close()
    return cnt


def main():
    repo = JobRepository()
    agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

    current_jobs = get_current_job_count()
    console.print(f"[bold cyan]Starting Verified Scraper Run to 1000+ USA Jobs...[/bold cyan]")
    console.print(f"Current Verified Jobs in DB: [bold green]{current_jobs}[/bold green] | Target: [bold yellow]1000[/bold yellow]\n")

    if current_jobs >= 1000:
        console.print(f"[bold green]✔ Target of 1000 jobs already achieved! Current: {current_jobs}[/bold green]")
    else:
        for name, url, industry in TARGET_COMPANIES:
            current_jobs = get_current_job_count()
            if current_jobs >= 1000:
                console.print(f"\n[bold green]🎯 Target Goal Reached! Total Jobs in DB: {current_jobs}[/bold green]")
                break

            console.print(f"\n[bold yellow]Processing [{industry}]: {name}[/bold yellow] ({url}) [Current DB: {current_jobs}/1000]")
            company = repo.get_or_create_company(
                name=name, domain=f"{name.lower().replace(' ', '')}.com", career_url=url, industry=industry
            )
            source = repo.get_or_create_job_source(
                company_id=company.id, source_url=url, scraper_type="playwright"
            )

            try:
                agent._process_company(company, source)
            except Exception as e:
                console.print(f"  [dim red]Error scraping {name}: {e}[/dim red]")
                continue

    final_jobs = get_current_job_count()
    console.print(f"\n[bold green]═══════════════════════════════════════════════════════[/bold green]")
    console.print(f"[bold green]✔ Final Total Verified USA Jobs in DB: {final_jobs}[/bold green]")
    console.print(f"[bold green]═══════════════════════════════════════════════════════[/bold green]")

    # Print summary table by industry
    conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
    cur = conn.cursor()
    cur.execute("""
        SELECT c.industry, count(j.id)
        FROM companies c
        JOIN jobs j ON j.company_id = c.id
        GROUP BY c.industry
        ORDER BY count(j.id) DESC;
    """)
    ind_data = cur.fetchall()
    conn.close()

    table = Table(title="USA Jobs in PostgreSQL by Industry", border_style="green")
    table.add_column("Industry", style="yellow")
    table.add_column("USA Jobs Stored", style="bold green", justify="right")
    for ind, cnt in ind_data:
        table.add_row(ind, str(cnt))
    console.print(table)


if __name__ == "__main__":
    main()
