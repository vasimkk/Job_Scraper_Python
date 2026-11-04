from typing import Dict, Type
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.greenhouse import GreenhouseScraper
from scraper_agent.scrapers.lever import LeverScraper
from scraper_agent.scrapers.ashby import AshbyScraper
from scraper_agent.scrapers.generic_html import GenericHtmlScraper

SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "greenhouse": GreenhouseScraper,
    "lever": LeverScraper,
    "ashby": AshbyScraper,
    "generic_html": GenericHtmlScraper,
}


def get_scraper_for_type(scraper_type: str) -> BaseScraper:
    """Factory function returning the instantiated scraper for a given scraper_type."""
    key = (scraper_type or "").strip().lower()
    scraper_cls = SCRAPER_REGISTRY.get(key)
    if not scraper_cls:
        # Fallback to generic_html
        return GenericHtmlScraper()
    return scraper_cls()

