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
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)

VERIFIED_SOURCES = [
    # 1. IT, Software & Technology
    ("Databricks", "https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    ("Figma", "https://boards.greenhouse.io/figma", "IT, Software & Technology"),
    ("Cloudflare", "https://boards.greenhouse.io/cloudflare", "IT, Software & Technology"),
    ("Datadog", "https://boards.greenhouse.io/datadog", "IT, Software & Technology"),
    ("Supabase", "https://boards.greenhouse.io/supabase", "IT, Software & Technology"),
    ("Notion", "https://boards.greenhouse.io/notion", "IT, Software & Technology"),
    ("Fastly", "https://boards.greenhouse.io/fastly", "IT, Software & Technology"),
    ("MongoDB", "https://boards.greenhouse.io/mongodb", "IT, Software & Technology"),
    ("Okta", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    ("Twilio", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("Gusto", "https://boards.greenhouse.io/gusto", "IT, Software & Technology"),
    ("Vercel", "https://boards.greenhouse.io/vercel", "IT, Software & Technology"),
    ("Linear", "https://jobs.ashbyhq.com/linear", "IT, Software & Technology"),
    ("Elastic", "https://boards.greenhouse.io/elastic", "IT, Software & Technology"),

    # 2. Healthcare
    ("Headway", "https://jobs.ashbyhq.com/headway", "Healthcare"),
    ("HealthVerity", "https://boards.greenhouse.io/healthverity", "Healthcare"),
    ("Komodo Health", "https://boards.greenhouse.io/komodohealth", "Healthcare"),
    ("Oscar Health", "https://boards.greenhouse.io/oscar", "Healthcare"),
    ("Doximity", "https://boards.greenhouse.io/doximity", "Healthcare"),
    ("Wheel", "https://boards.greenhouse.io/wheel", "Healthcare"),
    ("BetterHelp", "https://boards.greenhouse.io/betterhelp", "Healthcare"),
    ("Abby Care", "https://www.abbycare.org/careers", "Healthcare"),

    # 3. Finance & Banking
    ("Brex", "https://boards.greenhouse.io/brex", "Finance & Banking"),
    ("Ramp", "https://jobs.ashbyhq.com/ramp", "Finance & Banking"),
    ("Carta", "https://boards.greenhouse.io/carta", "Finance & Banking"),
    ("Blend", "https://boards.greenhouse.io/blend", "Finance & Banking"),
    ("Robinhood", "https://boards.greenhouse.io/robinhood", "Finance & Banking"),
    ("Wealthfront", "https://boards.greenhouse.io/wealthfront", "Finance & Banking"),
    ("Affirm", "https://boards.greenhouse.io/affirm", "Finance & Banking"),

    # 4. Insurance
    ("Coalition", "https://boards.greenhouse.io/coalition", "Insurance"),
    ("Cowbell Cyber", "https://boards.greenhouse.io/cowbellcyber", "Insurance"),
    ("Pie Insurance", "https://boards.greenhouse.io/pieinsurance", "Insurance"),
    ("Clearcover", "https://boards.greenhouse.io/clearcover", "Insurance"),
    ("Kin Insurance", "https://boards.greenhouse.io/kininsurance", "Insurance"),
    ("Hippo Insurance", "https://boards.greenhouse.io/hippo", "Insurance"),
    ("Root Insurance", "https://boards.greenhouse.io/rootinsurance", "Insurance"),
    ("Policygenius", "https://boards.greenhouse.io/policygenius", "Insurance"),

    # 5. Solar, Energy & Utilities
    ("Redwood Materials", "https://boards.greenhouse.io/redwoodmaterials", "Solar, Energy & Utilities"),
    ("ChargePoint", "https://boards.greenhouse.io/chargepoint", "Solar, Energy & Utilities"),
    ("Arcadia Power", "https://boards.greenhouse.io/arcadia", "Solar, Energy & Utilities"),
    ("Aurora Solar", "https://boards.greenhouse.io/aurorasolar", "Solar, Energy & Utilities"),
    ("Form Energy", "https://boards.greenhouse.io/formenergy", "Solar, Energy & Utilities"),

    # 6. Aerospace & Defense
    ("Anduril Industries", "https://www.anduril.com/open-roles", "Aerospace & Defense"),
    ("Astranis", "https://boards.greenhouse.io/astranis", "Aerospace & Defense"),
    ("Rocket Lab", "https://boards.greenhouse.io/rocketlab", "Aerospace & Defense"),
    ("BlackSky Technology", "https://boards.greenhouse.io/blacksky", "Aerospace & Defense"),
    ("Applied Intuition Defense", "https://boards.greenhouse.io/appliedintuition", "Aerospace & Defense"),
    ("Relativity Space", "https://boards.greenhouse.io/relativity", "Aerospace & Defense"),
    ("Planet Labs", "https://boards.greenhouse.io/planetlabs", "Aerospace & Defense"),
    ("Epirus", "https://boards.greenhouse.io/epirus", "Aerospace & Defense"),

    # 7. Pharma & Biotechnology
    ("Twist Bioscience", "https://boards.greenhouse.io/twistbioscience", "Pharma & Biotechnology"),
    ("Beam Therapeutics", "https://boards.greenhouse.io/beamtherapeutics", "Pharma & Biotechnology"),
    ("Ginkgo Bioworks", "https://boards.greenhouse.io/ginkgobioworks", "Pharma & Biotechnology"),
    ("Recursion Pharmaceuticals", "https://boards.greenhouse.io/recursion", "Pharma & Biotechnology"),
    ("Prime Medicine", "https://boards.greenhouse.io/primemedicine", "Pharma & Biotechnology"),

    # Extension High-Yield USA Companies (to surpass 1000+ jobs)
    ("Samsara", "https://boards.greenhouse.io/samsara", "IT, Software & Technology"),
    ("Roblox", "https://boards.greenhouse.io/roblox", "IT, Software & Technology"),
    ("Reddit", "https://boards.greenhouse.io/reddit", "IT, Software & Technology"),
    ("Scale AI", "https://boards.greenhouse.io/scaleai", "IT, Software & Technology"),
    ("Pure Storage", "https://boards.greenhouse.io/purestorage", "IT, Software & Technology"),
    ("Toast", "https://boards.greenhouse.io/toast", "Finance & Banking"),
    ("Coinbase", "https://boards.greenhouse.io/coinbase", "Finance & Banking"),
    ("Clover Health", "https://boards.greenhouse.io/cloverhealth", "Healthcare"),
    ("Rightway Healthcare", "https://boards.greenhouse.io/rightwayhealthcare", "Healthcare"),
    ("Span", "https://jobs.ashbyhq.com/span", "Solar, Energy & Utilities"),
    ("OpenAI", "https://jobs.ashbyhq.com/openai", "IT, Software & Technology"),
    ("Anthropic", "https://jobs.ashbyhq.com/anthropic", "IT, Software & Technology"),
    ("Chime", "https://boards.greenhouse.io/chime", "Finance & Banking"),
    ("SoFi", "https://boards.greenhouse.io/sofi", "Finance & Banking"),
    ("Pinterest", "https://boards.greenhouse.io/pinterest", "IT, Software & Technology"),
    ("Box", "https://boards.greenhouse.io/boxinc", "IT, Software & Technology"),
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
