"""
Batch Scraper Runner:
Evenly scrapes across all 7 Target Industries in round-robin fashion
to populate 1,000+ real USA-only tech jobs (Full-Time & Contract only)
into the PostgreSQL database.
"""
import sys
import os
from pathlib import Path

# Set temp directory on D: to prevent disk space issues
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import psycopg
from rich.console import Console
from rich.table import Table
from scraper_agent.db.repository import JobRepository
from scraper_agent.discovery.company_finder import DynamicJobDiscovery, TARGET_INDUSTRIES
from scraper_agent.agent.scraper_agent import ScraperAgent

console = Console(highlight=False)


def get_current_stats():
    conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM jobs;")
    total_jobs = cur.fetchone()[0]
    
    cur.execute("""
        SELECT c.industry, count(j.id) 
        FROM companies c 
        JOIN jobs j ON j.company_id = c.id 
        GROUP BY c.industry;
    """)
    ind_breakdown = dict(cur.fetchall())
    
    cur.execute("SELECT company_id, count(*) FROM jobs GROUP BY company_id;")
    company_job_counts = dict(cur.fetchall())
    
    conn.close()
    return total_jobs, ind_breakdown, company_job_counts


def run_batch_scrape(target_total_jobs: int = 1000):
    repo = JobRepository()
    discovery = DynamicJobDiscovery(headless=True)
    agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

    total_jobs, ind_breakdown, company_job_counts = get_current_stats()
    console.print(f"\n[bold cyan]╔════════════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print(f"[bold cyan]║ AutoJobApply – Multi-Industry Batch Scraper (Target: {target_total_jobs})  ║[/bold cyan]")
    console.print(f"[bold cyan]╚════════════════════════════════════════════════════════════════╝[/bold cyan]")
    console.print(f"Current USA Jobs in PostgreSQL: [bold green]{total_jobs}[/bold green] / [bold yellow]{target_total_jobs}[/bold yellow]\n")

    if total_jobs >= target_total_jobs:
        console.print(f"[bold green]✔ Target of {target_total_jobs} jobs already reached in database![/bold green]")
        return

    # Load all companies and sources grouped by industry
    industry_queue = {}
    for industry in TARGET_INDUSTRIES:
        comp_sources = discovery.find_companies_in_industry(industry)
        # Prioritize companies with 0 jobs, and prioritize ATS domains (greenhouse, lever, ashby, workday)
        def sort_priority(item):
            comp, src = item
            existing = company_job_counts.get(comp.id, 0)
            url_str = (src.source_url or "").lower()
            is_ats = 0 if any(a in url_str for a in ["greenhouse", "lever", "ashby", "open-roles", "workday", "jobvite"]) else 1
            return (is_ats, existing)

        sorted_list = sorted(comp_sources, key=sort_priority)
        industry_queue[industry] = sorted_list

    # Round-robin across industries until target reached
    round_num = 1
    while total_jobs < target_total_jobs:
        console.print(f"\n[bold magenta]═══════ Round-Robin Pass {round_num} Across 7 Industries ═══════[/bold magenta]")
        progress_made_in_pass = False

        for industry in TARGET_INDUSTRIES:
            total_jobs, _, company_job_counts = get_current_stats()
            if total_jobs >= target_total_jobs:
                break

            queue = industry_queue.get(industry, [])
            if not queue:
                continue

            # Pick next candidate company from this industry
            company, source = queue.pop(0)
            current_co_jobs = company_job_counts.get(company.id, 0)
            if current_co_jobs >= 40:
                continue

            console.print(
                f"\n[bold blue]🏢 [{industry}][/bold blue] Scraping [bold]{company.name}[/bold] "
                f"({source.source_url}) [dim][Current DB: {total_jobs}/{target_total_jobs}][/dim]"
            )

            try:
                agent._process_company(company, source)
                new_total, _, company_job_counts = get_current_stats()
                if new_total > total_jobs:
                    progress_made_in_pass = True
                    total_jobs = new_total
            except Exception as exc:
                console.print(f"  [dim red]Error scraping {company.name}: {exc}[/dim red]")
                continue

        round_num += 1
        if not progress_made_in_pass and round_num > 10:
            console.print("[yellow]Notice: Pass completed without new jobs; checking remaining pool...[/yellow]")
            break

    # Final summary
    total_jobs, ind_breakdown, _ = get_current_stats()
    console.print(f"\n[bold green]═══════════════════════════════════════════════════════[/bold green]")
    console.print(f"[bold green]✔ Batch Scrape Complete! Total USA Jobs in DB: {total_jobs}[/bold green]")
    console.print(f"[bold green]═══════════════════════════════════════════════════════[/bold green]")
    
    table = Table(title="Jobs in Database by Industry", border_style="cyan")
    table.add_column("Industry", style="yellow")
    table.add_column("USA Jobs Stored", style="bold green", justify="right")
    for ind, cnt in sorted(ind_breakdown.items(), key=lambda x: x[1], reverse=True):
        table.add_row(ind, str(cnt))
    console.print(table)


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run_batch_scrape(target)
