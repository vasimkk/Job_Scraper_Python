import os
import sys
sys.path.insert(0, ".")
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

scraper = PlaywrightCareerScraper(headless=True)

test_urls = [
    # Workday Healthcare
    ('Humana (Workday)', 'https://humana.wd5.myworkdayjobs.com/Humana_External_Career_Site'),
    ('DaVita (Workday)', 'https://davita.wd1.myworkdayjobs.com/DaVitaCareers'),
    ('Quest Diagnostics (Workday)', 'https://questdiagnostics.wd1.myworkdayjobs.com/quest_careers'),
    ('Labcorp (Workday)', 'https://labcorp.wd1.myworkdayjobs.com/ExternalCareerSite'),
    ('McKesson (Workday)', 'https://mckesson.wd3.myworkdayjobs.com/McKesson_Careers'),
    ('Cardinal Health (Workday)', 'https://cardinalhealth.wd1.myworkdayjobs.com/cardinal_health_careers'),
    ('Centene (Workday)', 'https://centene.wd1.myworkdayjobs.com/CenteneCareers'),
    # Jobvite Healthcare
    ('Zocdoc (Jobvite)', 'https://jobs.jobvite.com/zocdoc'),
    ('Health Catalyst (Jobvite)', 'https://jobs.jobvite.com/healthcatalyst'),
    ('Premier Inc (Jobvite)', 'https://jobs.jobvite.com/premierinc'),
    # iCIMS Healthcare
    ('Option Care Health (iCIMS)', 'https://careers-optioncarehealth.icims.com/jobs/search'),
    ('Lifepoint Health (iCIMS)', 'https://careers-lifepointhealth.icims.com/jobs/search'),
    ('Select Medical (iCIMS)', 'https://careers-selectmedical.icims.com/jobs/search'),
    # BambooHR Healthcare
    ('TherapyNotes (BambooHR)', 'https://therapynotes.bamboohr.com/careers'),
    ('MedTrainer (BambooHR)', 'https://medtrainer.bamboohr.com/careers'),
    # SmartRecruiters Healthcare
    ('Catholic Health (SmartRecruiters)', 'https://jobs.smartrecruiters.com/CatholicHealth'),
    ('Fresenius (SmartRecruiters)', 'https://jobs.smartrecruiters.com/FreseniusMedicalCareNorthAmerica'),
    # Taleo Healthcare
    ('Encompass Health (Taleo)', 'https://encompasshealth.taleo.net/careersection/2/jobsearch.ftl'),
]

for name, url in test_urls:
    try:
        jobs = scraper.scrape_career_page(url, max_jobs=5)
        title = jobs[0].title if jobs else 'None'
        print(f'[RESULT] {name}: {len(jobs)} jobs found! Sample: {title}')
    except Exception as e:
        print(f'[FAILED] {name}: {e}')
