import sys
sys.path.insert(0, ".")
import urllib.request
import json

candidates = [
    ("Catholic Health", "https://jobs.smartrecruiters.com/CatholicHealth"),
    ("Schneider Electric", "https://jobs.smartrecruiters.com/SchneiderElectric"),
    ("Visa", "https://jobs.smartrecruiters.com/Visa"),
    ("Square", "https://jobs.smartrecruiters.com/Square"),
    ("OpenAI", "https://jobs.ashbyhq.com/openai"),
    ("Ramp", "https://jobs.ashbyhq.com/ramp"),
    ("Notion", "https://jobs.ashbyhq.com/notion"),
    ("Linear", "https://jobs.ashbyhq.com/linear"),
    ("Synthesia", "https://jobs.ashbyhq.com/synthesia"),
    ("Headway", "https://jobs.ashbyhq.com/headway"),
    ("Abby Care", "https://jobs.ashbyhq.com/abbycare"),
    ("Anduril", "https://jobs.lever.co/anduril"),
    ("Astranis", "https://jobs.lever.co/astranis"),
    ("Shield AI", "https://jobs.lever.co/shieldai"),
    ("Stripe", "https://jobs.lever.co/stripe"),
    ("Atlassian", "https://jobs.lever.co/atlassian"),
]

from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

scraper = PlaywrightCareerScraper(headless=True)
for name, url in candidates:
    jobs = scraper.scrape_career_page(url, max_jobs=20)
    print(f"{name}: {len(jobs)} jobs scraped from {url}")
