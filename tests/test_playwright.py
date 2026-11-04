import unittest
import os
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper


class TestPlaywrightScraper(unittest.TestCase):

    def test_playwright_instantiation(self):
        scraper = PlaywrightCareerScraper(headless=True)
        self.assertIsNotNone(scraper)

    def test_playwright_real_career_page(self):
        scraper = PlaywrightCareerScraper(headless=True)
        # Test scraping a live Greenhouse board via Playwright
        jobs = scraper.scrape_career_page("https://boards.greenhouse.io/oscar", max_jobs=5)
        self.assertTrue(len(jobs) > 0, "Expected Playwright to extract jobs from Oscar Health career page")
        job = jobs[0]
        self.assertTrue(len(job.title) > 0)
        self.assertTrue(len(job.job_url) > 0)
        print(f"\n[Playwright Test Success] Extracted {len(jobs)} jobs. Sample: {job.title} | {job.job_url}")


if __name__ == "__main__":
    unittest.main()

