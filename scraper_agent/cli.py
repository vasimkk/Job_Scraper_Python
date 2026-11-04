import argparse
import sys
import os

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from scraper_agent.db.schema_manager import initialize_schema, seed_database
from scraper_agent.db.connection import test_connection
from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)


def print_database_stats():
    """Displays formatted statistics about the database."""
    repo = JobRepository()
    stats = repo.get_dashboard_summary()

    console.print("\n[bold cyan]============= ScraperAgent Database Overview =============[/bold cyan]")
    console.print(f"Total Companies: [bold green]{stats['total_companies']}[/bold green]")
    console.print(f"Active Job Sources: [bold green]{stats['active_sources']}[/bold green]")
    console.print(f"Total Jobs Stored: [bold green]{stats['total_jobs']}[/bold green]\n")

    # Industry Table
    ind_table = Table(title="Jobs by Industry", border_style="cyan")
    ind_table.add_column("Industry", style="yellow")
    ind_table.add_column("Jobs Count", style="bold green", justify="right")
    for row in stats["by_industry"]:
        ind_table.add_row(row["industry"] or "Unclassified", str(row["job_count"]))
    console.print(ind_table)

    # Employment Type Table
    emp_table = Table(title="Jobs by Employment Type", border_style="magenta")
    emp_table.add_column("Employment Type", style="cyan")
    emp_table.add_column("Count", style="bold green", justify="right")
    for row in stats["by_employment_type"]:
        emp_table.add_row(row["emp_type"], str(row["count"]))
    console.print(emp_table)

    # Remote Type Table
    rem_table = Table(title="Jobs by Remote Type", border_style="blue")
    rem_table.add_column("Remote Type", style="cyan")
    rem_table.add_column("Count", style="bold green", justify="right")
    for row in stats["by_remote_type"]:
        rem_table.add_row(row["remote_type"], str(row["count"]))
    console.print(rem_table)
    console.print()


def run_interactive_mode():
    """Interactive CLI menu to choose industry and run scraping."""
    repo = JobRepository()
    industries = repo.get_distinct_industries()

    console.print("\n[bold cyan]Select Target Industry:[/bold cyan]")
    console.print("  [bold green]0.[/bold green] ALL Industries")
    for idx, ind in enumerate(industries, 1):
        console.print(f"  [bold green]{idx}.[/bold green] {ind}")

    choice = Prompt.ask(
        "Enter industry number or name",
        default="0",
    )

    selected_industry = "ALL"
    if choice.isdigit():
        choice_idx = int(choice)
        if 1 <= choice_idx <= len(industries):
            selected_industry = industries[choice_idx - 1]
    elif choice in industries:
        selected_industry = choice

    agent = ScraperAgent()
    agent.start(target_industry=selected_industry)


def main():
    parser = argparse.ArgumentParser(
        description="AutoJobApply - Job Scraper Agent with PostgreSQL Storage"
    )
    parser.add_argument(
        "-i",
        "--industry",
        type=str,
        help="Target industry (e.g., 'Information Technology', 'Finance', 'Healthcare', 'Energy', 'Defense', 'ALL')",
    )
    parser.add_argument(
        "-c",
        "--company",
        type=str,
        help="Target specific company name (e.g. 'GitLab', 'Figma', 'Robinhood')",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database schema and seed companies and job sources",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display current statistics of companies and jobs in PostgreSQL",
    )
    parser.add_argument(
        "--all-jobs",
        action="store_true",
        help="Disable technology filter and scrape all job postings",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive console to select industry and parameters",
    )

    args = parser.parse_args()

    # Check connection first
    if not test_connection():
        console.print(
            "[bold red]Error:[/bold red] Cannot connect to PostgreSQL database. Please ensure PostgreSQL is running and check your .env settings."
        )
        sys.exit(1)

    if args.init_db:
        console.print("[cyan]Initializing database schema and seed data...[/cyan]")
        initialize_schema()
        seed_database()
        console.print("[bold green]✔ Database initialized and seeded successfully![/bold green]")
        return

    if args.stats:
        print_database_stats()
        return

    if args.interactive:
        run_interactive_mode()
        return

    # Normal Agent execution
    filter_tech = not args.all_jobs
    agent = ScraperAgent(filter_tech_only=filter_tech)
    agent.start(target_industry=args.industry, target_company=args.company)


if __name__ == "__main__":
    main()
