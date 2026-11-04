import unittest
from datetime import datetime, timezone
from scraper_agent.db.repository import JobRepository
from scraper_agent.db.connection import test_connection, get_db_connection
from scraper_agent.models.job import ProcessedJob, ScrapeRunStats
from scraper_agent.scrapers.base import BaseScraper


class TestIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not test_connection():
            raise unittest.SkipTest("Database not reachable.")

    def test_repository_industries_and_companies(self):
        repo = JobRepository()
        industries = repo.get_distinct_industries()
        self.assertIn("Information Technology", industries)
        self.assertIn("Finance", industries)

        tech_companies = repo.get_companies_by_industry("Information Technology")
        self.assertTrue(len(tech_companies) > 0)
        self.assertTrue(any(c.name == "GitLab" for c in tech_companies))

    def test_job_upsert_lifecycle(self):
        repo = JobRepository()
        company = repo.get_company_by_name("GitLab")
        self.assertIsNotNone(company)

        sources = repo.get_active_sources_for_company(company.id)
        self.assertTrue(len(sources) > 0)
        source = sources[0]

        ext_id = "test_unit_job_9999"
        title = "Staff Python Platform Engineer"
        desc = "Architecting cloud backend systems."
        loc = "San Francisco, CA"
        emp_type = "FULL_TIME"
        hash1 = BaseScraper.compute_content_hash(title, desc, loc, emp_type)

        job = ProcessedJob(
            company_id=company.id,
            source_id=source.id,
            external_job_id=ext_id,
            title=title,
            description=desc,
            location=loc,
            city="San Francisco",
            state="CA",
            country="United States",
            remote_type="REMOTE",
            employment_type=emp_type,
            posted_at=datetime.now(timezone.utc),
            source_updated_at=datetime.now(timezone.utc),
            job_url="https://about.gitlab.com/jobs/test-9999",
            application_url="https://about.gitlab.com/jobs/test-9999/apply",
            content_hash=hash1,
            is_tech=True,
            tech_keywords=["python", "engineer"],
            status="OPEN",
        )

        try:
            # 1. Insert new
            res1 = repo.upsert_job(job)
            self.assertIn(res1, ("NEW", "DUPLICATE"))

            # 2. Duplicate check (same hash)
            res2 = repo.upsert_job(job)
            self.assertEqual(res2, "DUPLICATE")

            # 3. Content updated
            job.description = "Updated description with new team requirements."
            job.content_hash = BaseScraper.compute_content_hash(
                job.title, job.description, job.location, job.employment_type
            )
            res3 = repo.upsert_job(job)
            self.assertEqual(res3, "UPDATED")

        finally:
            # Clean up test row
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM jobs WHERE company_id = %s AND external_job_id = %s",
                        (company.id, ext_id),
                    )


if __name__ == "__main__":
    unittest.main()

