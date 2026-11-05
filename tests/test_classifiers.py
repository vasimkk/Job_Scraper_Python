import unittest
from scraper_agent.classifiers.tech_filter import is_technology_job
from scraper_agent.classifiers.employment import classify_employment_type
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location


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

        # Unspecified / Remote noise cases
        city, state, country, remote_type = parse_location("Remote / Unspecified")
        self.assertIsNone(city)
        self.assertEqual(remote_type, "REMOTE")
        self.assertEqual(country, "United States")

        city, state, country, remote_type = parse_location("/ Unspecified")
        self.assertIsNone(city)

        # Single city resolution
        city, state, country, remote_type = parse_location("San Francisco")
        self.assertEqual(city, "San Francisco")
        self.assertEqual(state, "CA")
        self.assertEqual(country, "United States")

        # International parsing
        city, state, country, _ = parse_location("Bengaluru, India")
        self.assertEqual(country, "India")
        self.assertFalse(is_usa_location("Bengaluru, India"))

        city, state, country, _ = parse_location("London, United Kingdom")
        self.assertEqual(country, "United Kingdom")
        self.assertFalse(is_usa_location("London, United Kingdom"))

        city, state, country, _ = parse_location("Toronto, Canada")
        self.assertEqual(country, "Canada")
        self.assertFalse(is_usa_location("Toronto, Canada"))

        # ATS patterns
        city, state, country, _ = parse_location("US-CA-Campbell-254")
        self.assertEqual(state, "CA")
        self.assertEqual(country, "United States")
        self.assertTrue(is_usa_location("US-CA-Campbell-254"))

        city, state, country, _ = parse_location("IN-Karnataka-Bangalore")
        self.assertEqual(country, "India")
        self.assertFalse(is_usa_location("IN-Karnataka-Bangalore"))

    def test_usa_location_filter(self):
        # US Positive
        self.assertTrue(is_usa_location("San Francisco, CA"))
        self.assertTrue(is_usa_location("Austin, TX"))
        self.assertTrue(is_usa_location("Remote (US)"))
        self.assertTrue(is_usa_location("United States - Remote"))
        self.assertTrue(is_usa_location("US-CA-Campbell-254"))
        self.assertTrue(is_usa_location("Seattle, WA"))

        # Non-US Negative
        self.assertFalse(is_usa_location("Bengaluru, Karnataka, India"))
        self.assertFalse(is_usa_location("London, England, United Kingdom"))
        self.assertFalse(is_usa_location("Toronto, Ontario, Canada"))
        self.assertFalse(is_usa_location("Paris, France"))
        self.assertFalse(is_usa_location("Berlin, Germany"))
        self.assertFalse(is_usa_location("Tokyo, Japan"))
        self.assertFalse(is_usa_location("Sydney, Australia"))
        self.assertFalse(is_usa_location("Singapore"))
        self.assertFalse(is_usa_location("IN-HR-Gurugram-418"))
        self.assertFalse(is_usa_location("Where are you applying from? Europe North America"))


if __name__ == "__main__":
    unittest.main()

