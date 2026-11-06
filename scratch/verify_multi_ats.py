import os
import sys
import json
import urllib.request
sys.path.insert(0, ".")
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

scraper = PlaywrightCareerScraper(headless=True)

test_candidates = [
    # Workday
    ("Humana", "https://humana.wd5.myworkdayjobs.com/Humana_External_Career_Site"),
    ("DaVita", "https://davita.wd1.myworkdayjobs.com/DaVitaCareers"),
    ("Quest Diagnostics", "https://questdiagnostics.wd1.myworkdayjobs.com/quest_careers"),
    ("Cardinal Health", "https://cardinalhealth.wd1.myworkdayjobs.com/cardinal_health_careers"),
    ("Pfizer", "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"),
    ("Salesforce", "https://salesforce.wd1.myworkdayjobs.com/External_Career_Site"),
    ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
    ("Adobe", "https://adobe.wd5.myworkdayjobs.com/external_experienced"),
    ("Lockheed Martin", "https://lockheedmartin.wd5.myworkdayjobs.com/Lockheed_Martin_Careers"),
    ("Raytheon Technologies", "https://rtx.wd1.myworkdayjobs.com/RTX_Careers"),
    ("Northrop Grumman", "https://northropgrumman.wd1.myworkdayjobs.com/Northrop_Grumman_External_Career_Site"),
    ("Boeing", "https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS"),
    ("Capital One", "https://capitalone.wd1.myworkdayjobs.com/Capital_One"),
    ("Bank of America", "https://bankofamerica.wd1.myworkdayjobs.com/Bank_of_America"),
    ("Fidelity Investments", "https://fidelity.wd1.myworkdayjobs.com/FidelityCareers"),
    ("Sunrun", "https://sunrun.wd1.myworkdayjobs.com/Sunrun_Careers"),
    ("NextEra Energy", "https://nexteraenergy.wd5.myworkdayjobs.com/NextEra_Energy"),
    ("Travelers", "https://travelers.wd5.myworkdayjobs.com/External"),
    ("Prudential", "https://prudential.wd5.myworkdayjobs.com/PrudentialCareers"),
    ("Bristol Myers Squibb", "https://bms.wd5.myworkdayjobs.com/BMS"),
    ("Gilead Sciences", "https://gilead.wd1.myworkdayjobs.com/gileadcareers"),
    ("Amgen", "https://amgen.wd1.myworkdayjobs.com/Careers"),
    ("Regeneron", "https://regeneron.wd1.myworkdayjobs.com/Regeneron_Careers"),
    # Jobvite
    ("Zocdoc", "https://jobs.jobvite.com/zocdoc"),
    ("Health Catalyst", "https://jobs.jobvite.com/healthcatalyst"),
    ("Premier Inc", "https://jobs.jobvite.com/premierinc"),
    # SmartRecruiters
    ("Catholic Health", "https://jobs.smartrecruiters.com/CatholicHealth"),
    ("Square / Block", "https://jobs.smartrecruiters.com/Square"),
    ("Visa", "https://jobs.smartrecruiters.com/Visa"),
    ("Twitter", "https://jobs.smartrecruiters.com/Twitter"),
    ("Schneider Electric", "https://jobs.smartrecruiters.com/SchneiderElectric"),
    # BambooHR
    ("TherapyNotes", "https://therapynotes.bamboohr.com/careers"),
    ("MedTrainer", "https://medtrainer.bamboohr.com/careers"),
    # Ashby
    ("Headway", "https://jobs.ashbyhq.com/headway"),
    ("Abby Care", "https://jobs.ashbyhq.com/abbycare"),
    ("Ramp", "https://jobs.ashbyhq.com/ramp"),
    ("OpenAI", "https://jobs.ashbyhq.com/openai"),
    ("Linear", "https://jobs.ashbyhq.com/linear"),
    # Lever
    ("Color Health", "https://jobs.lever.co/color"),
    ("Forward Health", "https://jobs.lever.co/forward"),
    ("Anduril", "https://jobs.lever.co/anduril"),
    ("Anthropic", "https://jobs.lever.co/anthropic"),
    # Greenhouse
    ("Oscar Health", "https://boards.greenhouse.io/oscar"),
    ("Komodo Health", "https://boards.greenhouse.io/komodohealth"),
    ("Reddit", "https://boards.greenhouse.io/reddit"),
]

print(f"Testing {len(test_candidates)} candidates across all ATS platforms...", flush=True)

results = {}
for name, url in test_candidates:
    try:
        jobs = scraper.scrape_career_page(url, max_jobs=3)
        count = len(jobs)
        sample = jobs[0].title if count > 0 else "None"
        print(f"[OK] {name} ({count} jobs) -> {sample}", flush=True)
        results[name] = {"url": url, "count": count, "sample": sample}
    except Exception as e:
        print(f"[FAIL] {name}: {e}", flush=True)

with open("scratch/verified_multi_ats_test.json", "w") as f:
    json.dump(results, f, indent=2)
print("Finished testing all ATS candidates!", flush=True)
