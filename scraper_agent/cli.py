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
from scraper_agent.discovery.company_finder import (
    TARGET_INDUSTRIES,
    SUPPORTED_ATS_PLATFORMS,
    normalize_industry_name,
)
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
    """Interactive CLI menu to choose ATS platform first and run across all industries simultaneously."""
    # Step 1: ATS Platform Selection first
    console.print("\n[bold cyan]Step 1: Select Target ATS Platform:[/bold cyan]")
    console.print("  [bold green]0.[/bold green] ALL Supported ATS Platforms (Dice, Workday, Greenhouse, Lever, Ashby, SmartRecruiters, Jobvite, Taleo, etc.)")
    for idx, ats in enumerate(SUPPORTED_ATS_PLATFORMS[1:], 1):
        console.print(f"  [bold green]{idx}.[/bold green] {ats}")

    ats_choice = Prompt.ask(
        "Enter ATS selection (number or name)",
        default="0",
    )
    selected_ats = "ALL"
    if ats_choice.isdigit():
        c_idx = int(ats_choice)
        if c_idx == 0:
            selected_ats = "ALL"
        elif 1 <= c_idx < len(SUPPORTED_ATS_PLATFORMS):
            selected_ats = SUPPORTED_ATS_PLATFORMS[c_idx]
    elif ats_choice.strip():
        selected_ats = ats_choice.strip()

    # Step 2: Target Industry (Defaults to ALL 7 Target Industries simultaneously)
    console.print(f"\n[bold cyan]Step 2: Target Industry Coverage for [yellow]{selected_ats}[/yellow] ATS:[/bold cyan]")
    console.print("  [bold green]0.[/bold green] ALL 7 Target Industries (Simultaneous discovery across IT, Healthcare, Finance, Defense, Energy, Insurance, Pharma)")
    for idx, ind in enumerate(TARGET_INDUSTRIES, 1):
        console.print(f"  [bold green]{idx}.[/bold green] {ind}")
    console.print("  [bold green]C.[/bold green] Custom Industry (Type your own, e.g. 'FinTech', 'E-Commerce')")

    choice = Prompt.ask(
        "Enter industry selection (press Enter for ALL 7 Industries)",
        default="0",
    )

    selected_industry = "ALL"
    if choice.upper() == "C":
        selected_industry = Prompt.ask("Enter custom industry name", default="IT, Software & Technology")
    elif choice.isdigit():
        choice_idx = int(choice)
        if choice_idx == 0:
            selected_industry = "ALL"
        elif 1 <= choice_idx <= len(TARGET_INDUSTRIES):
            selected_industry = TARGET_INDUSTRIES[choice_idx - 1]
    elif choice in TARGET_INDUSTRIES:
        selected_industry = choice
    elif choice.strip():
        selected_industry = normalize_industry_name(choice.strip())

    # Step 3: Target Jobs Goal
    target_jobs_input = Prompt.ask(
        "Enter Target Jobs Goal (e.g. 12000, 0 for unlimited)",
        default="12000",
    )
    target_jobs = int(target_jobs_input) if target_jobs_input.isdigit() else 12000

    agent = ScraperAgent(enforce_date_window=enforce_date_window)
    agent.start(
        target_industry=selected_industry,
        target_ats=selected_ats,
        dynamic_discovery=True,
        target_jobs=target_jobs,
    )


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
        "-a",
        "--ats",
        type=str,
        default="ALL",
        help="Target ATS platform (e.g., 'Dice', 'Workday', 'Greenhouse', 'Lever', 'Ashby', 'SmartRecruiters', 'Jobvite', 'Taleo', 'ALL')",
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
    parser.add_argument(
        "--target-jobs",
        type=int,
        default=0,
        help="Target total number of jobs to store in the database (e.g. 12000)",
    )
    parser.add_argument(
        "--limit-per-industry",
        type=int,
        default=0,
        help="Maximum companies to scrape per industry",
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

    if args.interactive:
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
                target_ats=args.ats,
                dynamic_discovery=dynamic_disc,
                target_jobs=args.target_jobs,
            )
            sleep_secs = args.interval * 3600
            console.print(f"[dim]Next daily scrape in {args.interval} hour(s). Sleeping...[/dim]")
            time.sleep(sleep_secs)

    # Single-run execution (directly starts across all ATS platforms and industries without prompts)
    ats_label = args.ats.upper() if args.ats else "ALL"
    ind_label = args.industry or "ALL 7 Target Industries"
    console.print(
        f"[bold green]▶ Direct Execution:[/bold green] Processing [cyan]{ats_label}[/cyan] ATS platforms across [yellow]{ind_label}[/yellow]..."
    )

    agent = ScraperAgent(
        filter_tech_only=filter_tech,
        enforce_date_window=enforce_dates,
    )
    agent.start(
        target_industry=args.industry,
        target_company=args.company,
        target_url=args.url,
        target_ats=args.ats,
        dynamic_discovery=dynamic_disc,
        target_jobs=args.target_jobs,
        limit_per_industry=args.limit_per_industry,
    )


if __name__ == "__main__":
    main()
