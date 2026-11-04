import unittest
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.registry import get_scraper_for_type
from scraper_agent.scrapers.greenhouse import GreenhouseScraper
from scraper_agent.scrapers.lever import LeverScraper
from scraper_agent.scrapers.ashby import AshbyScraper
from scraper_agent.scrapers.generic_html import GenericHtmlScraper


class TestScrapers(unittest.TestCase):

    def test_clean_html(self):
        html_input = "<p>We are seeking a <strong>Python Engineer</strong> to join our team.</p><ul><li>5+ years experience</li></ul>"
        cleaned = BaseScraper.clean_html(html_input)
        self.assertIn("Python Engineer", cleaned)
        self.assertIn("5+ years experience", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("<strong>", cleaned)

    def test_content_hash_consistency(self):
        h1 = BaseScraper.compute_content_hash(
            "Backend Engineer", "Building APIs", "Remote", "FULL_TIME"
        )
        h2 = BaseScraper.compute_content_hash(
            "Backend Engineer", "Building APIs", "Remote", "FULL_TIME"
        )
        h3 = BaseScraper.compute_content_hash(
            "Backend Engineer", "Building APIs Updated", "Remote", "FULL_TIME"
        )
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)

    def test_scraper_registry(self):
        self.assertIsInstance(get_scraper_for_type("greenhouse"), GreenhouseScraper)
        self.assertIsInstance(get_scraper_for_type("lever"), LeverScraper)
        self.assertIsInstance(get_scraper_for_type("ashby"), AshbyScraper)
        self.assertIsInstance(get_scraper_for_type("unknown_type"), GenericHtmlScraper)


if __name__ == "__main__":
    unittest.main()

