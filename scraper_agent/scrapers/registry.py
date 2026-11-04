from typing import Dict, Type
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.generic_html import GenericHtmlScraper
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "playwright": PlaywrightCareerScraper,
    "generic_html": GenericHtmlScraper,
}


def get_scraper_for_type(scraper_type: str) -> BaseScraper:
    """
    Factory function returning the instantiated scraper for a given scraper_type.
    Defaults to PlaywrightCareerScraper for scraping career pages directly.
    """
    key = (scraper_type or "").strip().lower()
    scraper_cls = SCRAPER_REGISTRY.get(key)
    if not scraper_cls:
        # Default all career pages and unknown types to Playwright
        if key == "generic_html" or key == "html":
            return GenericHtmlScraper()
        return PlaywrightCareerScraper()
    return scraper_cls()
