import unittest
from scraper_agent.classifiers.jd_analyzer import JDAnalyzer


class TestJDAnalyzer(unittest.TestCase):

    def test_deduce_industry(self):
        # Healthcare JD
        health_jd = """
        We are building a telehealth platform that integrates with hospital EMR systems.
        The engineer will ensure HIPAA compliance and handle sensitive patient clinical data.
        """
        ind = JDAnalyzer.deduce_industry_from_jd("Software Engineer", health_jd)
        self.assertEqual(ind, "Healthcare")

        # Finance & Banking JD
        fin_jd = """
        Our fintech platform processes millions in daily credit card payments and crypto transactions.
        You will build secure banking ledgers and trading reconciliation pipelines.
        """
        ind = JDAnalyzer.deduce_industry_from_jd("Senior Engineer", fin_jd)
        self.assertEqual(ind, "Finance & Banking")

        # Aerospace & Defense JD
        defense_jd = """
        Developing autonomous UAV and drone systems for national security.
        Requires active DoD Secret security clearance and avionics radar integration.
        """
        ind = JDAnalyzer.deduce_industry_from_jd("Systems Architect", defense_jd)
        self.assertEqual(ind, "Aerospace & Defense")

        # Solar, Energy & Utilities JD
        energy_jd = """
        Join our clean energy mission! Building EV charging networks and smart power grid batteries
        to accelerate solar and renewable decarbonization.
        """
        ind = JDAnalyzer.deduce_industry_from_jd("Firmware Lead", energy_jd)
        self.assertEqual(ind, "Solar, Energy & Utilities")

        # Insurance JD
        insur_jd = """
        Our insurtech platform automates policyholder claims and underwriting actuarial models.
        """
        ind = JDAnalyzer.deduce_industry_from_jd("Software Engineer", insur_jd)
        self.assertEqual(ind, "Insurance")

        # Pharma & Biotechnology JD
        pharma_jd = """
        Working on mRNA therapeutics, oncology genomics, and FDA approved drug discovery assays.
        """
        ind = JDAnalyzer.deduce_industry_from_jd("Bioinformatics Developer", pharma_jd)
        self.assertEqual(ind, "Pharma & Biotechnology")

    def test_deduce_tech_role(self):
        # AI/ML
        role = JDAnalyzer.deduce_tech_role_from_jd(
            "Senior Machine Learning Engineer",
            "Training LLM transformers using PyTorch and fine-tuning GenAI models."
        )
        self.assertEqual(role, "AI / Machine Learning Engineer")

        # Data Engineer
        role = JDAnalyzer.deduce_tech_role_from_jd(
            "Staff Data Engineer",
            "Building high-throughput ETL data pipelines using Snowflake, Spark, and Airflow."
        )
        self.assertEqual(role, "Data Engineer")

        # Backend
        role = JDAnalyzer.deduce_tech_role_from_jd(
            "Backend Engineer (Python / Go)",
            "Developing scalable REST and GraphQL microservices with PostgreSQL."
        )
        self.assertEqual(role, "Backend Engineer")

        # Frontend
        role = JDAnalyzer.deduce_tech_role_from_jd(
            "Frontend Developer",
            "Building responsive web applications using React, Next.js, and TypeScript."
        )
        self.assertEqual(role, "Frontend Engineer")

        # DevOps / SRE
        role = JDAnalyzer.deduce_tech_role_from_jd(
            "Site Reliability Engineer (SRE)",
            "Managing Kubernetes clusters, Terraform infrastructure, and Prometheus monitoring."
        )
        self.assertEqual(role, "DevOps / SRE / Platform Engineer")

    def test_deduce_employment_type(self):
        # Contract
        emp = JDAnalyzer.deduce_employment_type_from_jd(
            "React Developer (Contract)",
            "6-month C2C / 1099 contractor engagement."
        )
        self.assertEqual(emp, "CONTRACT")

        # Part-time
        emp = JDAnalyzer.deduce_employment_type_from_jd(
            "Junior Web Assistant - Part Time",
            "Flexible 20 hours per week role."
        )
        self.assertEqual(emp, "PART_TIME")

        # Internship
        emp = JDAnalyzer.deduce_employment_type_from_jd(
            "Summer Software Engineering Intern",
            "3-month student internship program."
        )
        self.assertEqual(emp, "INTERNSHIP")

        # Full-time with vendor/contract mentions in JD text
        emp = JDAnalyzer.deduce_employment_type_from_jd(
            "Construction Quality Assurance/Quality Control Manager, EPC",
            "Coordinate third-party special inspections and audit contractor turnover. The position is full-time."
        )
        self.assertEqual(emp, "FULL_TIME")

        # Full-time
        emp = JDAnalyzer.deduce_employment_type_from_jd(
            "Staff Platform Architect",
            "Full-time permanent salaried position with full medical and 401k benefits."
        )
        self.assertEqual(emp, "FULL_TIME")


if __name__ == "__main__":
    unittest.main()

