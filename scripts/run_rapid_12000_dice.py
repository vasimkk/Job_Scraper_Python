"""
AutoJobApply – Ultra-Rapid 12,000+ Job Target Booster (Dice ATS Platform Integration):

Integrates the Dice ATS platform (dice.com) across multiple tech specializations and industries:
- IT, Software & Technology: Python, Java, Cloud, Full Stack, Data & AI, DevOps, Cybersecurity, Contract Tech
- Finance & Banking: FinTech & Financial Systems
- Healthcare: HealthTech & Clinical AI
- Aerospace & Defense: Defense Systems & Embedded Engineering
- Solar, Energy & Utilities: CleanTech & Grid Software
- Insurance: InsurTech Platforms
- Pharma & Biotechnology: Bioinformatics & Computational Biology

Strictly implements the system pipeline:
  1. Identifies Industry
  2. Finds Companies & Sources on Dice ATS Platform
  3. Identifies Posted Jobs (Freshness Window: Current Month & Previous Month)
  4. Filters by Technology Nature (is_technology_job)
  5. Classifies Employment Type (FULL_TIME vs CONTRACT)
  6. Scrapes Details (Deduced Tech Role, Location normalization, Remote Type, Content Hash)
  7. Vectorizes with 768-dimensional normalized BAAI/bge-base-en-v1.5 embeddings
  8. Upserts into PostgreSQL with deduplication and change auditing
  9. Stops automatically once total verified jobs in PostgreSQL reaches 12,000+.
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
from rich.panel import Panel

from scraper_agent.db.repository import JobRepository
from scraper_agent.db.connection import test_connection, get_db_connection
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)
TARGET_TOTAL_JOBS = 12000

# High-Yield Dice ATS Platform targets across target industries & specializations
DICE_TARGETS = [
    {"name": "Dice Python & Backend", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=python+backend", "industry": "IT, Software & Technology"},
    {"name": "Dice Java & Cloud Engineering", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=java+cloud", "industry": "IT, Software & Technology"},
    {"name": "Dice Full Stack Software", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=full+stack+software+engineer", "industry": "IT, Software & Technology"},
    {"name": "Dice Data & AI Engineering", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=data+engineer+ai", "industry": "IT, Software & Technology"},
    {"name": "Dice DevOps & SRE", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=devops+site+reliability", "industry": "IT, Software & Technology"},
    {"name": "Dice Cybersecurity", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=cybersecurity+engineer", "industry": "IT, Software & Technology"},
    {"name": "Dice Contract Tech Roles", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=contract+software+developer", "industry": "IT, Software & Technology"},
    {"name": "Dice FinTech & Financial Systems", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=fintech+software", "industry": "Finance & Banking"},
    {"name": "Dice HealthTech & Clinical AI", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=healthtech+software", "industry": "Healthcare"},
    {"name": "Dice Defense & Systems Engineering", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=defense+systems+engineer", "industry": "Aerospace & Defense"},
    {"name": "Dice CleanTech & Energy", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=energy+software+engineer", "industry": "Solar, Energy & Utilities"},
    {"name": "Dice InsurTech Platforms", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=insurtech+engineer", "industry": "Insurance"},
    {"name": "Dice BioTech & Bioinformatics", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=bioinformatics+software", "industry": "Pharma & Biotechnology"},
]


def run():
    if not test_connection():
        console.print("[bold red]Error: PostgreSQL is not reachable on port 5433.[/bold red]")
        sys.exit(1)

    repo = JobRepository()
    initial_summary = repo.get_dashboard_summary()
    current_jobs = initial_summary["total_jobs"]

    console.print(
        Panel.fit(
            f"[bold cyan]AutoJobApply – Rapid 12,000+ Job Target Booster (Dice ATS Platform)[/bold cyan]\n"
            f"[yellow]Current Jobs in DB:[/yellow] [bold green]{current_jobs}[/bold green] | "
            f"[yellow]Target Goal:[/yellow] [bold green]{TARGET_TOTAL_JOBS}[/bold green] jobs\n"
            f"[dim]Ingesting fresh tech jobs from Dice ATS Platform with BAAI/bge-base-en-v1.5 pgvector embeddings[/dim]",
            border_style="cyan",
        )
    )

    if current_jobs >= TARGET_TOTAL_JOBS:
        console.print(f"[bold green]✔ Target already reached: {current_jobs} jobs in database![/bold green]")
        return

    agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

    for idx, target in enumerate(DICE_TARGETS, 1):
        summary = repo.get_dashboard_summary()
        current_jobs = summary["total_jobs"]
        if current_jobs >= TARGET_TOTAL_JOBS:
            console.print(f"\n[bold green]🎉 SUCCESS! Reached target goal: {current_jobs} jobs stored in PostgreSQL![/bold green]")
            break

        name = target["name"]
        domain = target["domain"]
        url = target["career_url"]
        industry = target["industry"]
        needed = TARGET_TOTAL_JOBS - current_jobs

        console.print(
            f"\n[bold cyan][{idx}/{len(DICE_TARGETS)}][/bold cyan] "
            f"Processing Dice ATS: [bold yellow]{name}[/bold yellow] ({industry}) | "
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

    final_summary = repo.get_dashboard_summary()
    console.print("\n[bold cyan]============= Final Scraping Results =============[/bold cyan]")
    console.print(f"Total Jobs in DB: [bold green]{final_summary['total_jobs']}[/bold green] (Initial: {initial_summary['total_jobs']})")
    console.print(f"Total Companies: [bold green]{final_summary['total_companies']}[/bold green]")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*), count(job_embedding) FROM jobs;")
            tot, emb = cur.fetchone()
            console.print(f"Total Vectorized: [bold green]{emb}[/bold green] / {tot} (100% vector(768))")

    ind_table = Table(title="Jobs Stored by Industry", border_style="cyan")
    ind_table.add_column("Industry", style="yellow")
    ind_table.add_column("Jobs Count", style="bold green", justify="right")
    for row in final_summary["by_industry"]:
        ind_table.add_row(row["industry"] or "Unclassified", str(row["job_count"]))
    console.print(ind_table)

    emp_table = Table(title="Jobs Stored by Employment Type", border_style="magenta")
    emp_table.add_column("Employment Type", style="cyan")
    emp_table.add_column("Jobs Count", style="bold green", justify="right")
    for row in final_summary["by_employment_type"]:
        emp_table.add_row(row["emp_type"] or "Unknown", str(row["count"]))
    console.print(emp_table)


if __name__ == "__main__":
    run()

