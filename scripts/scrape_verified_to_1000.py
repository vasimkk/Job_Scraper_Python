"""
Targeted Scraper Runner:
Scrapes verified high-yield company career sources across the 7 target industries
until total verified USA jobs in PostgreSQL reaches 1,000+.
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
from scraper_agent.models.job import Company, JobSource
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)

VERIFIED_SOURCES = [
    # 1. Insurance
    ("Coalition", "https://boards.greenhouse.io/coalition", "Insurance"),
    ("Cowbell Cyber", "https://boards.greenhouse.io/cowbellcyber", "Insurance"),
    ("Pie Insurance", "https://boards.greenhouse.io/pieinsurance", "Insurance"),

    # 2. Healthcare
    ("HealthVerity", "https://boards.greenhouse.io/healthverity", "Healthcare"),
    ("Headway", "https://jobs.ashbyhq.com/headway", "Healthcare"),
    ("Komodo Health", "https://boards.greenhouse.io/komodohealth", "Healthcare"),
    ("Doximity", "https://boards.greenhouse.io/doximity", "Healthcare"),

    # 3. Aerospace & Defense
    ("Relativity Space", "https://boards.greenhouse.io/relativity", "Aerospace & Defense"),
    ("Planet Labs", "https://boards.greenhouse.io/planetlabs", "Aerospace & Defense"),
    ("Epirus", "https://boards.greenhouse.io/epirus", "Aerospace & Defense"),

    # 4. Pharma & Biotechnology
    ("Twist Bioscience", "https://boards.greenhouse.io/twistbioscience", "Pharma & Biotechnology"),
    ("Beam Therapeutics", "https://boards.greenhouse.io/beamtherapeutics", "Pharma & Biotechnology"),
    ("Ginkgo Bioworks", "https://boards.greenhouse.io/ginkgobioworks", "Pharma & Biotechnology"),

    # 5. IT, Software & Technology
    ("Databricks", "https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    ("Okta", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    ("MongoDB", "https://boards.greenhouse.io/mongodb", "IT, Software & Technology"),
    ("Fastly", "https://boards.greenhouse.io/fastly", "IT, Software & Technology"),
    ("Twilio", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("Gusto", "https://boards.greenhouse.io/gusto", "IT, Software & Technology"),

    # 6. Finance & Banking
    ("Brex", "https://boards.greenhouse.io/brex", "Finance & Banking"),
    ("Ramp", "https://jobs.ashbyhq.com/ramp", "Finance & Banking"),
    ("Carta", "https://boards.greenhouse.io/carta", "Finance & Banking"),
    ("Blend", "https://boards.greenhouse.io/blend", "Finance & Banking"),
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
    console.print(f"[bold cyan]Starting Target Scraper to reach 1000+ USA jobs...[/bold cyan]")
    console.print(f"Current Jobs in DB: [bold green]{current_jobs}[/bold green] | Target: [bold yellow]1000[/bold yellow]\n")

    if current_jobs >= 1000:
        console.print(f"[bold green]✔ Target of 1000 jobs already achieved! Current: {current_jobs}[/bold green]")
        return

    for name, url, industry in VERIFIED_SOURCES:
        current_jobs = get_current_job_count()
        if current_jobs >= 1000:
            console.print(f"\n[bold green]🎯 Target Goal Reached! Total Jobs in DB: {current_jobs}[/bold green]")
            break

        console.print(f"\n[bold yellow]Processing [{industry}]: {name}[/bold yellow] ({url})")
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
    console.print(f"[bold green]✔ Execution Complete! Final Total USA Jobs in DB: {final_jobs}[/bold green]")
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

