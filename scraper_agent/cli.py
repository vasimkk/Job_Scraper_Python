import argparse
import sys
import os
import time

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from scraper_agent.db.schema_manager import initialize_schema, seed_database
from scraper_agent.db.connection import test_connection
from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent
from scraper_agent.classifiers.date_filter import format_freshness_window_description

console = Console(highlight=False)


def print_database_stats():
    """Displays formatted statistics about the database."""
    repo = JobRepository()
    stats = repo.get_dashboard_summary()

    console.print("\n[bold cyan]============= ScraperAgent Database Overview =============[/bold cyan]")
    console.print(f"Total Companies in DB: [bold green]{stats['total_companies']}[/bold green]")
    console.print(f"Active Job Sources: [bold green]{stats['active_sources']}[/bold green]")
    console.print(f"Total Jobs Stored: [bold green]{stats['total_jobs']}[/bold green]")
    console.print(f"Active Freshness Filter: [dim]{format_freshness_window_description()}[/dim]\n")

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

    # Tech Roles Table (Deduced from JD)
    if "by_tech_role" in stats and stats["by_tech_role"]:
        role_table = Table(title="Top Tech Roles (Deduced from JD)", border_style="green")
        role_table.add_column("Tech Role", style="yellow")
        role_table.add_column("Count", style="bold green", justify="right")
        for row in stats["by_tech_role"][:12]:
            role_table.add_row(row["tech_role"], str(row["count"]))
        console.print(role_table)
    console.print()


def run_interactive_mode(enforce_date_window: bool = True):
    """Interactive CLI menu to choose industry and run dynamic scraping."""
    repo = JobRepository()
    industries = repo.get_distinct_industries()

    console.print("\n[bold cyan]Select Target Industry for Dynamic Discovery:[/bold cyan]")
    console.print("  [bold green]0.[/bold green] ALL Industries (Broad Dynamic Discovery)")
    for idx, ind in enumerate(industries, 1):
        console.print(f"  [bold green]{idx}.[/bold green] {ind}")
    console.print("  [bold green]C.[/bold green] Custom Industry (Type your own, e.g. 'Cybersecurity', 'FinTech')")

    choice = Prompt.ask(
        "Enter selection (number, name, or custom industry)",
        default="0",
    )

    selected_industry = "ALL"
    if choice.upper() == "C":
        selected_industry = Prompt.ask("Enter custom industry name", default="Information Technology")
    elif choice.isdigit():
        choice_idx = int(choice)
        if 1 <= choice_idx <= len(industries):
            selected_industry = industries[choice_idx - 1]
    elif choice in industries:
        selected_industry = choice
    elif choice.strip():
        selected_industry = choice.strip()

    agent = ScraperAgent(enforce_date_window=enforce_date_window)
    agent.start(target_industry=selected_industry, dynamic_discovery=True)


def main():
    parser = argparse.ArgumentParser(
        description="AutoJobApply - Dynamic Job Scraper Agent with Date Window & PostgreSQL Storage"
    )
    parser.add_argument(
        "-i",
        "--industry",
        type=str,
        help="Target industry for dynamic discovery (e.g., 'Information Technology', 'Finance', 'Healthcare', 'Energy', 'Defense', 'ALL')",
    )
    parser.add_argument(
        "-c",
        "--company",
        type=str,
        help="Target specific company name",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="Directly scrape a real company career page URL using Playwright (e.g. 'https://www.figma.com/careers')",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database schema and seed default companies",
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
        "--all-dates",
        action="store_true",
        help="Disable date window filter (by default only current month & previous month jobs are kept)",
    )
    parser.add_argument(
        "--no-discovery",
        action="store_true",
        help="Disable dynamic web feed discovery (only scrape pre-existing DB sources)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive console to select industry and parameters",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Run continuously as a daily scraper, repeating every interval (default 24 hours)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="Interval in hours for --daily mode (default: 24 hours)",
    )

    args = parser.parse_args()

    # Check connection first
    if not test_connection():
        console.print(
            "[bold red]Error:[/bold red] Cannot connect to PostgreSQL database. Please ensure PostgreSQL is running and check your .env settings."
        )
        sys.exit(1)

    if args.init_db:
        console.print("[cyan]Initializing database schema...[/cyan]")
        initialize_schema()
        seed_database()
        console.print("[bold green]✔ Database initialized successfully![/bold green]")
        return

    if args.stats:
        print_database_stats()
        return

    enforce_dates = not args.all_dates
    dynamic_disc = not args.no_discovery
    filter_tech = not args.all_jobs

    if args.interactive or len(sys.argv) == 1:
        run_interactive_mode(enforce_date_window=enforce_dates)
        return

    # Daily continuous mode
    if args.daily:
        console.print(
            f"[bold cyan]Starting Daily Scraper Agent (Running every {args.interval} hours)...[/bold cyan]"
        )
        while True:
            agent = ScraperAgent(
                filter_tech_only=filter_tech,
                enforce_date_window=enforce_dates,
            )
            agent.start(
                target_industry=args.industry,
                target_company=args.company,
                target_url=args.url,
                dynamic_discovery=dynamic_disc,
            )
            sleep_secs = args.interval * 3600
            console.print(f"[dim]Next daily scrape in {args.interval} hour(s). Sleeping...[/dim]")
            time.sleep(sleep_secs)

    # Single-run execution
    agent = ScraperAgent(
        filter_tech_only=filter_tech,
        enforce_date_window=enforce_dates,
    )
    agent.start(
        target_industry=args.industry,
        target_company=args.company,
        target_url=args.url,
        dynamic_discovery=dynamic_disc,
    )


if __name__ == "__main__":
    main()
