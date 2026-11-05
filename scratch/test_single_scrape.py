import sys
sys.path.insert(0, ".")
from scraper_agent.agent.scraper_agent import ScraperAgent

agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)
agent.start(target_industry="Aerospace & Defense", target_company="Anduril Industries")

