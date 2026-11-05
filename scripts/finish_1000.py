"""
Final Step to 1,000+ Verified Active USA Jobs:
Scrapes Twilio, Okta, GitLab, Oscar Health until DB >= 1000.
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

FINAL_COMPANIES = [
    ("Twilio", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("Okta", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    ("GitLab", "https://boards.greenhouse.io/gitlab", "IT, Software & Technology"),
    ("Oscar Health", "https://boards.greenhouse.io/oscar", "Healthcare"),
    ("BetterHelp", "https://boards.greenhouse.io/betterhelp", "Healthcare"),
    ("Astranis", "https://boards.greenhouse.io/astranis", "Aerospace & Defense"),
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
    console.print(f"[bold cyan]Starting Final Push to 1000+ USA Jobs...[/bold cyan]")
    console.print(f"Current Verified Jobs in DB: [bold green]{current_jobs}[/bold green] | Target: [bold yellow]1000[/bold yellow]\n")

    if current_jobs >= 1000:
        console.print(f"[bold green]✔ Target of 1000 jobs already achieved! Current: {current_jobs}[/bold green]")
    else:
        for name, url, industry in FINAL_COMPANIES:
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
    console.print(f"[bold green]✔ Final Total Verified Active USA Jobs in DB: {final_jobs}[/bold green]")
    console.print(f"[bold green]═══════════════════════════════════════════════════════[/bold green]")

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

    table = Table(title="Verified Active USA Jobs in PostgreSQL by Industry", border_style="green")
    table.add_column("Industry", style="yellow")
    table.add_column("USA Jobs Stored", style="bold green", justify="right")
    for ind, cnt in ind_data:
        table.add_row(ind, str(cnt))
    console.print(table)


if __name__ == "__main__":
    main()

