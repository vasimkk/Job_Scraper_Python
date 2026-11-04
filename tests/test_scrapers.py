import unittest
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.registry import get_scraper_for_type
from scraper_agent.scrapers.generic_html import GenericHtmlScraper
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper


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
        self.assertIsInstance(get_scraper_for_type("playwright"), PlaywrightCareerScraper)
        self.assertIsInstance(get_scraper_for_type("generic_html"), GenericHtmlScraper)
        # Unknown/fallback types default to Playwright
        self.assertIsInstance(get_scraper_for_type("career_page"), PlaywrightCareerScraper)
        self.assertIsInstance(get_scraper_for_type("unknown"), PlaywrightCareerScraper)


if __name__ == "__main__":
    unittest.main()
