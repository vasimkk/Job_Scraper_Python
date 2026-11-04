from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.generic_html import GenericHtmlScraper
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper
from scraper_agent.scrapers.registry import get_scraper_for_type, SCRAPER_REGISTRY

__all__ = [
    "BaseScraper",
    "GenericHtmlScraper",
    "PlaywrightCareerScraper",
    "get_scraper_for_type",
    "SCRAPER_REGISTRY",
]
