import unittest
from scraper_agent.classifiers.tech_filter import is_technology_job
from scraper_agent.classifiers.employment import classify_employment_type
from scraper_agent.classifiers.location_parser import parse_location


class TestClassifiers(unittest.TestCase):

    def test_tech_filter_positive(self):
        tech_titles = [
            "Senior Backend Engineer (Python)",
            "Frontend Developer (React / Next.js)",
            "Staff DevOps / SRE Engineer",
            "Machine Learning Engineer - LLM Systems",
            "Lead Cloud Infrastructure Architect",
            "Data Scientist - NLP",
            "QA Automation Engineer",
            "Cybersecurity Analyst",
        ]
        for title in tech_titles:
            is_tech, keywords = is_technology_job(title)
            self.assertTrue(is_tech, f"Expected '{title}' to be recognized as tech")
            self.assertTrue(len(keywords) > 0)

    def test_tech_filter_negative(self):
        non_tech_titles = [
            "Registered Nurse - ICU",
            "Senior Accountant",
            "Clinical Specialist",
            "Receptionist & Office Assistant",
            "Corporate Legal Counsel",
            "Sales Representative",
        ]
        for title in non_tech_titles:
            is_tech, keywords = is_technology_job(title)
            self.assertFalse(is_tech, f"Expected '{title}' to be filtered out as non-tech")

    def test_employment_type_classification(self):
        self.assertEqual(
            classify_employment_type("Software Engineer (Contract)"),
            "CONTRACT"
        )
        self.assertEqual(
            classify_employment_type("Data Analyst - C2C / 1099"),
            "CONTRACT"
        )
        self.assertEqual(
            classify_employment_type("Senior Frontend Developer", description="This is a 6-month contract role."),
            "CONTRACT"
        )
        self.assertEqual(
            classify_employment_type("Cloud Architect (Full-time Regular)"),
            "FULL_TIME"
        )
        self.assertEqual(
            classify_employment_type("DevOps Engineer", source_metadata={"commitment": "Full Time"}),
            "FULL_TIME"
        )
        self.assertEqual(
            classify_employment_type("Staff Machine Learning Engineer"),
            "FULL_TIME"
        )

    def test_location_parser(self):
        # Remote
        city, state, country, remote_type = parse_location("San Francisco, CA (Remote)")
        self.assertEqual(remote_type, "REMOTE")
        self.assertEqual(state, "CA")
        self.assertEqual(country, "United States")

        # Hybrid
        city, state, country, remote_type = parse_location("New York, NY - Hybrid")
        self.assertEqual(remote_type, "HYBRID")

        # On-site
        city, state, country, remote_type = parse_location("Austin, TX")
        self.assertEqual(remote_type, "ON_SITE")
        self.assertEqual(state, "TX")
        self.assertEqual(country, "United States")


if __name__ == "__main__":
    unittest.main()

