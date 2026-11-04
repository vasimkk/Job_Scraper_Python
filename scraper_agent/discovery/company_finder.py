import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

# Ensure temp directory stays on D: to prevent disk space exhaustion
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from scraper_agent.db.repository import JobRepository
from scraper_agent.models.job import Company, JobSource, RawJobPost
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

logger = logging.getLogger(__name__)

# The 7 Canonical Target Industries
TARGET_INDUSTRIES = [
    "IT, Software & Technology",
    "Healthcare",
    "Finance & Banking",
    "Insurance",
    "Solar, Energy & Utilities",
    "Aerospace & Defense",
    "Pharma & Biotechnology",
]

# Verified real corporate career portals for the 7 Target Industries
VERIFIED_INDUSTRY_COMPANIES: Dict[str, List[Dict[str, str]]] = {
    "IT, Software & Technology": [
        {"name": "GitLab", "domain": "gitlab.com", "career_url": "https://about.gitlab.com/jobs"},
        {"name": "Linear", "domain": "linear.app", "career_url": "https://linear.app/careers"},
        {"name": "Figma", "domain": "figma.com", "career_url": "https://www.figma.com/careers"},
        {"name": "Datadog", "domain": "datadoghq.com", "career_url": "https://www.datadoghq.com/careers"},
        {"name": "Elastic", "domain": "elastic.co", "career_url": "https://www.elastic.co/about/careers"},
        {"name": "Synthesia", "domain": "synthesia.io", "career_url": "https://www.synthesia.io/careers"},
        {"name": "Vercel", "domain": "vercel.com", "career_url": "https://vercel.com/careers"},
        {"name": "Stripe", "domain": "stripe.com", "career_url": "https://stripe.com/jobs"},
        {"name": "GitHub", "domain": "github.com", "career_url": "https://github.com/about/careers"},
        {"name": "Cloudflare", "domain": "cloudflare.com", "career_url": "https://www.cloudflare.com/careers/"},
        {"name": "CrowdStrike", "domain": "crowdstrike.com", "career_url": "https://www.crowdstrike.com/careers/"},
    ],
    "Healthcare": [
        {"name": "Oscar Health", "domain": "hioscar.com", "career_url": "https://www.hioscar.com/careers"},
        {"name": "Doximity", "domain": "doximity.com", "career_url": "https://www.doximity.com/careers"},
        {"name": "Komodo Health", "domain": "komodohealth.com", "career_url": "https://www.komodohealth.com/careers"},
        {"name": "BetterHelp", "domain": "betterhelp.com", "career_url": "https://www.betterhelp.com/careers/"},
        {"name": "Wheel", "domain": "wheel.com", "career_url": "https://www.wheel.com/careers"},
        {"name": "Abby Care", "domain": "abbycare.org", "career_url": "https://www.abbycare.org/careers"},
        {"name": "Datavant", "domain": "datavant.com", "career_url": "https://datavant.com/careers"},
        {"name": "Ro", "domain": "ro.co", "career_url": "https://ro.co/careers"},
        {"name": "Teladoc Health", "domain": "teladochealth.com", "career_url": "https://www.teladochealth.com/about/careers/"},
        {"name": "GoodRx", "domain": "goodrx.com", "career_url": "https://www.goodrx.com/corporate/careers"},
    ],
    "Finance & Banking": [
        {"name": "Robinhood", "domain": "robinhood.com", "career_url": "https://robinhood.com/careers"},
        {"name": "Coinbase", "domain": "coinbase.com", "career_url": "https://www.coinbase.com/careers"},
        {"name": "Ramp", "domain": "ramp.com", "career_url": "https://ramp.com/careers"},
        {"name": "Wealthfront", "domain": "wealthfront.com", "career_url": "https://wealthfront.com/careers"},
        {"name": "Plaid", "domain": "plaid.com", "career_url": "https://plaid.com/careers"},
        {"name": "Brex", "domain": "brex.com", "career_url": "https://www.brex.com/careers"},
        {"name": "Affirm", "domain": "affirm.com", "career_url": "https://www.affirm.com/careers"},
        {"name": "Block", "domain": "block.xyz", "career_url": "https://block.xyz/careers"},
        {"name": "Chime", "domain": "chime.com", "career_url": "https://www.chime.com/careers/"},
        {"name": "SoFi", "domain": "sofi.com", "career_url": "https://www.sofi.com/careers/"},
    ],
    "Insurance": [
        {"name": "Lemonade", "domain": "lemonade.com", "career_url": "https://www.lemonade.com/careers"},
        {"name": "Root Insurance", "domain": "joinroot.com", "career_url": "https://www.joinroot.com/careers/"},
        {"name": "Hippo Insurance", "domain": "hippo.com", "career_url": "https://www.hippo.com/careers"},
        {"name": "Policygenius", "domain": "policygenius.com", "career_url": "https://www.policygenius.com/careers/"},
        {"name": "Kin Insurance", "domain": "kin.com", "career_url": "https://www.kin.com/careers/"},
        {"name": "Next Insurance", "domain": "nextinsurance.com", "career_url": "https://www.nextinsurance.com/careers/"},
    ],
    "Solar, Energy & Utilities": [
        {"name": "ChargePoint", "domain": "chargepoint.com", "career_url": "https://www.chargepoint.com/careers"},
        {"name": "Palmetto", "domain": "palmetto.com", "career_url": "https://palmetto.com/careers"},
        {"name": "Sunrun", "domain": "sunrun.com", "career_url": "https://careers.sunrun.com/"},
        {"name": "Enphase Energy", "domain": "enphase.com", "career_url": "https://enphase.com/careers"},
        {"name": "Form Energy", "domain": "formenergy.com", "career_url": "https://formenergy.com/careers"},
        {"name": "Rivian", "domain": "rivian.com", "career_url": "https://rivian.com/careers"},
        {"name": "Aurora Solar", "domain": "aurorasolar.com", "career_url": "https://aurorasolar.com/careers/"},
    ],
    "Aerospace & Defense": [
        {"name": "Anduril Industries", "domain": "anduril.com", "career_url": "https://www.anduril.com/careers"},
        {"name": "Palantir Technologies", "domain": "palantir.com", "career_url": "https://www.palantir.com/careers/"},
        {"name": "SpaceX", "domain": "spacex.com", "career_url": "https://www.spacex.com/careers/"},
        {"name": "Planet Labs", "domain": "planet.com", "career_url": "https://www.planet.com/careers/"},
        {"name": "Astranis", "domain": "astranis.com", "career_url": "https://www.astranis.com/careers"},
        {"name": "Relativity Space", "domain": "relativityspace.com", "career_url": "https://www.relativityspace.com/careers"},
        {"name": "Shield AI", "domain": "shield.ai", "career_url": "https://shield.ai/careers/"},
    ],
    "Pharma & Biotechnology": [
        {"name": "Moderna", "domain": "modernatx.com", "career_url": "https://modernatx.eightfold.ai/careers"},
        {"name": "Regeneron", "domain": "regeneron.com", "career_url": "https://careers.regeneron.com/"},
        {"name": "BioNTech", "domain": "biontech.com", "career_url": "https://biontech.com/int/en/home/careers.html"},
        {"name": "Vertex Pharmaceuticals", "domain": "vrtx.com", "career_url": "https://www.vrtx.com/careers/"},
        {"name": "Recursion Pharmaceuticals", "domain": "recursion.com", "career_url": "https://www.recursion.com/careers"},
        {"name": "Ginkgo Bioworks", "domain": "ginkgobioworks.com", "career_url": "https://www.ginkgobioworks.com/careers/"},
        {"name": "Tempus AI", "domain": "tempus.com", "career_url": "https://www.tempus.com/careers/"},
        {"name": "Illumina", "domain": "illumina.com", "career_url": "https://www.illumina.com/company/careers.html"},
    ],
}


def normalize_industry_name(raw_name: str) -> str:
    """Normalizes any alias or short name to the canonical 7 Target Industries."""
    if not raw_name or raw_name.strip().upper() == "ALL":
        return "ALL"
    c = raw_name.strip().lower()

    # Exact matches first
    for target in TARGET_INDUSTRIES:
        if c == target.lower():
            return target

    # Specific domains before generic IT
    if any(k in c for k in ["pharm", "bio", "therap"]):
        return "Pharma & Biotechnology"
    if any(k in c for k in ["insur", "policy"]):
        return "Insurance"
    if any(k in c for k in ["solar", "energy", "util", "power", "grid", "clean"]):
        return "Solar, Energy & Utilities"
    if any(k in c for k in ["aero", "defense", "defen", "space", "milit"]):
        return "Aerospace & Defense"
    if any(k in c for k in ["fin", "bank", "pay", "crypto", "trading"]):
        return "Finance & Banking"
    if any(k in c for k in ["health", "clinic", "hospital", "patient", "care"]):
        return "Healthcare"
    if re.search(r"\b(it|software|tech|technology|saas|cloud|computer)\b", c):
        return "IT, Software & Technology"

    return raw_name.strip()


class DynamicJobDiscovery:
    """
    Industry-based company discovery and career page scraper using Playwright.
    Follows the workflow:
      Identify Industry -> Find Companies in Industry -> Identify Posted Jobs directly from Career Pages.
    """

    def __init__(self, headless: bool = True):
        self.repo = JobRepository()
        self.playwright_scraper = PlaywrightCareerScraper(headless=headless)

    def scrape_custom_url(
        self, career_url: str, company_name: Optional[str] = None, industry: Optional[str] = None
    ) -> Tuple[Company, JobSource, List[RawJobPost]]:
        """Scrapes a specific real company career page URL directly using Playwright."""
        domain = self._extract_domain(career_url)
        name = company_name or (domain.split(".")[0].title() if domain else "Custom Company")
        ind = industry or "IT, Software & Technology"

        company = self.repo.get_or_create_company(
            name=name, domain=domain, career_url=career_url, industry=ind
        )
        source = self.repo.get_or_create_job_source(
            company_id=company.id, source_url=career_url, scraper_type="playwright"
        )
        raw_jobs = self.playwright_scraper.scrape_career_page(career_url)
        return company, source, raw_jobs

    def find_companies_in_industry(
        self, industry: str, company_filter: Optional[str] = None
    ) -> List[Tuple[Company, JobSource]]:
        """
        Flow Step 3: Find Companies in Industry.
        Retrieves companies belonging to the identified industry, along with their active career page sources.
        Automatically registers verified companies into PostgreSQL on-the-fly without needing seed_data.sql.
        """
        ind_clean = normalize_industry_name(industry)

        # 1. Check if matching companies already exist in the database
        matched_companies: List[Company] = []
        if company_filter:
            comp = self.repo.get_company_by_name(company_filter)
            if comp:
                matched_companies.append(comp)
        else:
            matched_companies = self.repo.get_companies_by_industry(ind_clean)

        # 2. If no companies exist in DB for this industry, dynamically populate from verified directory
        if not matched_companies and ind_clean in VERIFIED_INDUSTRY_COMPANIES:
            logger.info(f"Registering verified companies for industry '{ind_clean}' in database...")
            for comp_info in VERIFIED_INDUSTRY_COMPANIES[ind_clean]:
                comp = self.repo.get_or_create_company(
                    name=comp_info["name"],
                    domain=comp_info["domain"],
                    career_url=comp_info["career_url"],
                    industry=ind_clean,
                )
                self.repo.get_or_create_job_source(
                    company_id=comp.id,
                    source_url=comp_info["career_url"],
                    scraper_type="playwright",
                )
            matched_companies = self.repo.get_companies_by_industry(ind_clean)

        # 3. Build (Company, JobSource) pairs
        results: List[Tuple[Company, JobSource]] = []
        for comp in matched_companies:
            sources = self.repo.get_active_sources_for_company(comp.id)
            for src in sources:
                if src.scraper_type == "playwright" or "career" in src.source_url or "job" in src.source_url:
                    results.append((comp, src))
                    break
            else:
                if comp.career_url:
                    src = self.repo.get_or_create_job_source(
                        company_id=comp.id,
                        source_url=comp.career_url,
                        scraper_type="playwright",
                    )
                    results.append((comp, src))

        return results

    def identify_posted_jobs(
        self, source: JobSource, max_jobs: int = 50
    ) -> List[RawJobPost]:
        """
        Flow Step 4: Identify Posted Jobs.
        Opens the company's real career page URL using Playwright browser automation
        and extracts all active job postings.
        """
        logger.info(f"Opening career page with Playwright: {source.source_url}")
        return self.playwright_scraper.scrape_career_page(source.source_url, max_jobs=max_jobs)

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        if not url:
            return None
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            return netloc.replace("www.", "") if netloc else None
        except Exception:
            return None
