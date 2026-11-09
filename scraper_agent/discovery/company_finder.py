import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

# Ensure temp directory stays on D: if available to prevent disk space exhaustion
temp_dir = "D:\\Temp"
try:
    os.makedirs(temp_dir, exist_ok=True)
    os.environ["TEMP"] = temp_dir
    os.environ["TMP"] = temp_dir
except Exception:
    pass

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

# Supported ATS Platforms for Target Filtering
SUPPORTED_ATS_PLATFORMS = [
    "ALL",
    "Dice",
    "Workday",
    "Greenhouse",
    "Lever",
    "Ashby",
    "SmartRecruiters",
    "Jobvite",
    "Taleo",
    "BambooHR",
    "iCIMS",
]


def matches_ats(url: str, ats: Optional[str]) -> bool:
    """Checks whether a URL matches a specified ATS platform filter."""
    if not ats or ats.strip().upper() in ("ALL", ""):
        return True
    a = ats.strip().lower()
    u = (url or "").lower()
    if a in ("dice", "dise"):
        return "dice.com" in u
    if a in ("workday", "wd"):
        return "myworkdayjobs.com" in u
    if a == "greenhouse":
        return "greenhouse.io" in u
    if a == "lever":
        return "lever.co" in u
    if a == "ashby":
        return "ashbyhq.com" in u
    if a in ("smartrecruiters", "smart_recruiters"):
        return "smartrecruiters.com" in u
    if a == "jobvite":
        return "jobvite.com" in u
    if a == "taleo":
        return "taleo.net" in u
    if a == "bamboohr":
        return "bamboohr.com" in u
    if a == "icims":
        return "icims.com" in u
    return a in u


# Verified real corporate career portals across all ATS platforms for the 7 Target Industries
VERIFIED_INDUSTRY_COMPANIES: Dict[str, List[Dict[str, str]]] = {
    "IT, Software & Technology": [
        # Dice ATS Platform
        {"name": "Dice Tech Careers", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=software+engineer", "industry": "IT, Software & Technology"},
        {"name": "Dice Cloud & DevOps", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=cloud+devops", "industry": "IT, Software & Technology"},
        {"name": "Dice Data & AI", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=data+engineer", "industry": "IT, Software & Technology"},
        # Workday CXS
        {"name": "NVIDIA", "domain": "nvidia.com", "career_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"},
        {"name": "Salesforce", "domain": "salesforce.com", "career_url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site"},
        {"name": "Adobe", "domain": "adobe.com", "career_url": "https://adobe.wd5.myworkdayjobs.com/external_experienced"},
        {"name": "Workday", "domain": "workday.com", "career_url": "https://workday.wd5.myworkdayjobs.com/Workday"},
        {"name": "Broadcom", "domain": "broadcom.com", "career_url": "https://broadcom.wd1.myworkdayjobs.com/External_Career"},
        {"name": "Autodesk", "domain": "autodesk.com", "career_url": "https://autodesk.wd1.myworkdayjobs.com/Ext"},
        # SmartRecruiters
        {"name": "Square / Block", "domain": "squareup.com", "career_url": "https://jobs.smartrecruiters.com/Square"},
        # Ashby
        {"name": "OpenAI", "domain": "openai.com", "career_url": "https://jobs.ashbyhq.com/openai"},
        {"name": "Linear", "domain": "linear.app", "career_url": "https://jobs.ashbyhq.com/linear"},
        {"name": "Synthesia", "domain": "synthesia.io", "career_url": "https://jobs.ashbyhq.com/synthesia"},
        # Lever
        {"name": "Atlassian", "domain": "atlassian.com", "career_url": "https://jobs.lever.co/atlassian"},
        {"name": "Palantir", "domain": "palantir.com", "career_url": "https://jobs.lever.co/palantir"},
        {"name": "Dropbox", "domain": "dropbox.com", "career_url": "https://jobs.lever.co/dropbox"},
        {"name": "Snyk", "domain": "snyk.io", "career_url": "https://jobs.lever.co/snyk"},
        {"name": "Retool", "domain": "retool.com", "career_url": "https://jobs.lever.co/retool"},
        {"name": "Zapier", "domain": "zapier.com", "career_url": "https://jobs.lever.co/zapier"},
        # Greenhouse
        {"name": "Stripe", "domain": "stripe.com", "career_url": "https://boards.greenhouse.io/stripe"},
        {"name": "Waymo", "domain": "waymo.com", "career_url": "https://boards.greenhouse.io/waymo"},
        {"name": "Epic Games", "domain": "epicgames.com", "career_url": "https://boards.greenhouse.io/epicgames"},
        {"name": "Asana", "domain": "asana.com", "career_url": "https://boards.greenhouse.io/asana"},
        {"name": "Databricks", "domain": "databricks.com", "career_url": "https://boards.greenhouse.io/databricks"},
        {"name": "Figma", "domain": "figma.com", "career_url": "https://boards.greenhouse.io/figma"},
        {"name": "Cloudflare", "domain": "cloudflare.com", "career_url": "https://boards.greenhouse.io/cloudflare"},
        {"name": "Datadog", "domain": "datadoghq.com", "career_url": "https://boards.greenhouse.io/datadog"},
        {"name": "Snowflake", "domain": "snowflake.com", "career_url": "https://boards.greenhouse.io/snowflake"},
        {"name": "Reddit", "domain": "reddit.com", "career_url": "https://boards.greenhouse.io/reddit"},
        {"name": "Roblox", "domain": "roblox.com", "career_url": "https://boards.greenhouse.io/roblox"},
        {"name": "Pure Storage", "domain": "purestorage.com", "career_url": "https://boards.greenhouse.io/purestorage"},
        {"name": "MongoDB", "domain": "mongodb.com", "career_url": "https://boards.greenhouse.io/mongodb"},
        {"name": "Okta", "domain": "okta.com", "career_url": "https://boards.greenhouse.io/okta"},
        {"name": "Twilio", "domain": "twilio.com", "career_url": "https://boards.greenhouse.io/twilio"},
        {"name": "Box", "domain": "box.com", "career_url": "https://boards.greenhouse.io/box"},
        {"name": "GitLab", "domain": "gitlab.com", "career_url": "https://boards.greenhouse.io/gitlab"},
        {"name": "Elastic", "domain": "elastic.co", "career_url": "https://boards.greenhouse.io/elastic"},
        {"name": "Vercel", "domain": "vercel.com", "career_url": "https://boards.greenhouse.io/vercel"},
        {"name": "Scale AI", "domain": "scale.com", "career_url": "https://boards.greenhouse.io/scaleai"},
        {"name": "Gusto", "domain": "gusto.com", "career_url": "https://boards.greenhouse.io/gusto"},
        {"name": "Pinterest", "domain": "pinterest.com", "career_url": "https://boards.greenhouse.io/pinterest"},
        {"name": "HashiCorp", "domain": "hashicorp.com", "career_url": "https://boards.greenhouse.io/hashicorp"},
        {"name": "Cockroach Labs", "domain": "cockroachlabs.com", "career_url": "https://boards.greenhouse.io/cockroachlabs"},
        {"name": "Postman", "domain": "postman.com", "career_url": "https://boards.greenhouse.io/postman"},
        {"name": "Grafana Labs", "domain": "grafana.com", "career_url": "https://boards.greenhouse.io/grafanalabs"},
        {"name": "dbt Labs", "domain": "getdbt.com", "career_url": "https://boards.greenhouse.io/getdbt"},
        {"name": "Cisco", "domain": "cisco.com", "career_url": "https://cisco.wd5.myworkdayjobs.com/Cisco_Careers"},
        {"name": "HP Inc", "domain": "hp.com", "career_url": "https://hp.wd5.myworkdayjobs.com/ExternalCareerSite"},
        {"name": "Qualcomm", "domain": "qualcomm.com", "career_url": "https://qualcomm.wd5.myworkdayjobs.com/External"},
        {"name": "Palo Alto Networks", "domain": "paloaltonetworks.com", "career_url": "https://paloaltonetworks.wd1.myworkdayjobs.com/careers"},
        {"name": "Western Digital", "domain": "wdc.com", "career_url": "https://westerndigital.wd1.myworkdayjobs.com/WDC_Careers"},
        {"name": "Samsara", "domain": "samsara.com", "career_url": "https://boards.greenhouse.io/samsara"},
        {"name": "Klaviyo", "domain": "klaviyo.com", "career_url": "https://boards.greenhouse.io/klaviyo"},
        {"name": "DoorDash", "domain": "doordash.com", "career_url": "https://boards.greenhouse.io/doordash"},
        {"name": "Instacart", "domain": "instacart.com", "career_url": "https://boards.greenhouse.io/instacart"},
        {"name": "Uber", "domain": "uber.com", "career_url": "https://boards.greenhouse.io/uber"},
        {"name": "Lyft", "domain": "lyft.com", "career_url": "https://boards.greenhouse.io/lyft"},
        {"name": "Airbnb", "domain": "airbnb.com", "career_url": "https://boards.greenhouse.io/airbnb"},
        {"name": "Notion", "domain": "notion.so", "career_url": "https://jobs.ashbyhq.com/notion"},
        {"name": "Airtable", "domain": "airtable.com", "career_url": "https://boards.greenhouse.io/airtable"},
        {"name": "Rippling", "domain": "rippling.com", "career_url": "https://boards.greenhouse.io/rippling"},
        {"name": "Verkada", "domain": "verkada.com", "career_url": "https://boards.greenhouse.io/verkada"},
        {"name": "Snap", "domain": "snap.com", "career_url": "https://boards.greenhouse.io/snap"},
        {"name": "Splunk", "domain": "splunk.com", "career_url": "https://boards.greenhouse.io/splunk"},
        {"name": "Zoom", "domain": "zoom.us", "career_url": "https://boards.greenhouse.io/zoom"},
        {"name": "Confluent", "domain": "confluent.io", "career_url": "https://boards.greenhouse.io/confluent"},
        {"name": "SentinelOne", "domain": "sentinelone.com", "career_url": "https://boards.greenhouse.io/sentinelone"},
        {"name": "Cohesity", "domain": "cohesity.com", "career_url": "https://boards.greenhouse.io/cohesity"},
        {"name": "Rubrik", "domain": "rubrik.com", "career_url": "https://boards.greenhouse.io/rubrik"},
        {"name": "Tanium", "domain": "tanium.com", "career_url": "https://boards.greenhouse.io/tanium"},
        {"name": "Wiz", "domain": "wiz.io", "career_url": "https://jobs.ashbyhq.com/wiz"},
        {"name": "Anthropic", "domain": "anthropic.com", "career_url": "https://jobs.ashbyhq.com/anthropic"},
        {"name": "Perplexity", "domain": "perplexity.ai", "career_url": "https://jobs.ashbyhq.com/perplexity"},
        {"name": "Supabase", "domain": "supabase.com", "career_url": "https://jobs.ashbyhq.com/supabase"},
        {"name": "Pinecone", "domain": "pinecone.io", "career_url": "https://boards.greenhouse.io/pinecone"},
        {"name": "Weaviate", "domain": "weaviate.io", "career_url": "https://boards.greenhouse.io/weaviate"},
        {"name": "Weights & Biases", "domain": "wandb.ai", "career_url": "https://boards.greenhouse.io/wandb"},
    ],
    "Healthcare": [
        # Dice ATS Platform
        {"name": "Dice HealthTech", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=healthcare+software", "industry": "Healthcare"},
        # Workday CXS
        {"name": "Humana", "domain": "humana.com", "career_url": "https://humana.wd5.myworkdayjobs.com/Humana_External_Career_Site"},
        {"name": "Medtronic", "domain": "medtronic.com", "career_url": "https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers"},
        {"name": "Stryker", "domain": "stryker.com", "career_url": "https://stryker.wd1.myworkdayjobs.com/StrykerCareers"},
        {"name": "Danaher", "domain": "danaher.com", "career_url": "https://danaher.wd1.myworkdayjobs.com/DanaherJobs"},
        # SmartRecruiters
        {"name": "Catholic Health", "domain": "chsbuffalo.org", "career_url": "https://jobs.smartrecruiters.com/CatholicHealth"},
        # Jobvite
        {"name": "Zocdoc", "domain": "zocdoc.com", "career_url": "https://jobs.jobvite.com/zocdoc"},
        {"name": "Health Catalyst", "domain": "healthcatalyst.com", "career_url": "https://jobs.jobvite.com/healthcatalyst"},
        {"name": "Premier Inc", "domain": "premierinc.com", "career_url": "https://jobs.jobvite.com/premierinc"},
        # Taleo
        {"name": "Encompass Health", "domain": "encompasshealth.com", "career_url": "https://encompasshealth.taleo.net/careersection/2/jobsearch.ftl"},
        # Ashby
        {"name": "Headway", "domain": "headway.co", "career_url": "https://jobs.ashbyhq.com/headway"},
        {"name": "Abby Care", "domain": "abbycare.org", "career_url": "https://jobs.ashbyhq.com/abbycare"},
        # Lever
        {"name": "Color Health", "domain": "color.com", "career_url": "https://jobs.lever.co/color"},
        {"name": "Forward Health", "domain": "goforward.com", "career_url": "https://jobs.lever.co/forward"},
        # Greenhouse
        {"name": "Oscar Health", "domain": "hioscar.com", "career_url": "https://boards.greenhouse.io/oscar"},
        {"name": "Komodo Health", "domain": "komodohealth.com", "career_url": "https://boards.greenhouse.io/komodohealth"},
        {"name": "Tempus AI", "domain": "tempus.com", "career_url": "https://boards.greenhouse.io/tempus"},
        {"name": "Ro", "domain": "ro.co", "career_url": "https://boards.greenhouse.io/ro"},
        {"name": "Datavant", "domain": "datavant.com", "career_url": "https://boards.greenhouse.io/datavant"},
        {"name": "GoodRx", "domain": "goodrx.com", "career_url": "https://boards.greenhouse.io/goodrx"},
        {"name": "Hinge Health", "domain": "hingehealth.com", "career_url": "https://boards.greenhouse.io/hingehealth"},
        {"name": "Maven Clinic", "domain": "mavenclinic.com", "career_url": "https://boards.greenhouse.io/mavenclinic"},
        {"name": "Flatiron Health", "domain": "flatiron.com", "career_url": "https://boards.greenhouse.io/flatironhealth"},
        {"name": "Cedar", "domain": "cedar.com", "career_url": "https://boards.greenhouse.io/cedar"},
        {"name": "Lyra Health", "domain": "lyrahealth.com", "career_url": "https://boards.greenhouse.io/lyrahealth"},
        {"name": "Omada Health", "domain": "omadahealth.com", "career_url": "https://boards.greenhouse.io/omadahealth"},
        {"name": "Clover Health", "domain": "cloverhealth.com", "career_url": "https://boards.greenhouse.io/cloverhealth"},
        {"name": "HealthVerity", "domain": "healthverity.com", "career_url": "https://boards.greenhouse.io/healthverity"},
        {"name": "SonderMind", "domain": "sondermind.com", "career_url": "https://boards.greenhouse.io/sondermind"},
        {"name": "Wheel", "domain": "wheel.com", "career_url": "https://boards.greenhouse.io/wheel"},
        {"name": "BetterHelp", "domain": "betterhelp.com", "career_url": "https://boards.greenhouse.io/betterhelp"},
        {"name": "Doximity", "domain": "doximity.com", "career_url": "https://boards.greenhouse.io/doximity"},
        {"name": "Abbott", "domain": "abbott.com", "career_url": "https://abbott.wd5.myworkdayjobs.com/abbottcareers"},
        {"name": "Cardinal Health", "domain": "cardinalhealth.com", "career_url": "https://cardinalhealth.wd1.myworkdayjobs.com/EXT"},
        {"name": "Boston Scientific", "domain": "bostonscientific.com", "career_url": "https://bostonscientific.wd1.myworkdayjobs.com/BSC"},
        {"name": "Baxter", "domain": "baxter.com", "career_url": "https://baxter.wd1.myworkdayjobs.com/baxter"},
        {"name": "Cigna", "domain": "cigna.com", "career_url": "https://cigna.wd5.myworkdayjobs.com/cigna"},
        {"name": "Tenet Healthcare", "domain": "tenethealth.com", "career_url": "https://tenet.wd1.myworkdayjobs.com/Tenet_Careers"},
        {"name": "DaVita", "domain": "davita.com", "career_url": "https://davita.wd1.myworkdayjobs.com/DaVita_Careers"},
        {"name": "Quest Diagnostics", "domain": "questdiagnostics.com", "career_url": "https://questdiagnostics.wd1.myworkdayjobs.com/Quest_Careers"},
        {"name": "Cityblock Health", "domain": "cityblock.com", "career_url": "https://boards.greenhouse.io/cityblockhealth"},
        {"name": "Carbon Health", "domain": "carbonhealth.com", "career_url": "https://boards.greenhouse.io/carbonhealth"},
        {"name": "Alto Pharmacy", "domain": "alto.com", "career_url": "https://boards.greenhouse.io/altopharmacy"},
        {"name": "One Medical", "domain": "onemedical.com", "career_url": "https://boards.greenhouse.io/onemedical"},
        {"name": "Oak Street Health", "domain": "oakstreethealth.com", "career_url": "https://boards.greenhouse.io/oakstreethealth"},
        {"name": "Spring Health", "domain": "springhealth.com", "career_url": "https://jobs.ashbyhq.com/springhealth"},
        {"name": "K Health", "domain": "khealth.com", "career_url": "https://boards.greenhouse.io/khealth"},
        {"name": "Ribbon Health", "domain": "ribbonhealth.com", "career_url": "https://boards.greenhouse.io/ribbonhealth"},
    ],
    "Finance & Banking": [
        # Dice ATS Platform
        {"name": "Dice FinTech", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=fintech+developer", "industry": "Finance & Banking"},
        # Workday CXS
        {"name": "US Bank", "domain": "usbank.com", "career_url": "https://usbank.wd1.myworkdayjobs.com/US_Bank_Careers"},
        # SmartRecruiters
        {"name": "Visa", "domain": "visa.com", "career_url": "https://jobs.smartrecruiters.com/Visa"},
        # Ashby
        {"name": "Ramp", "domain": "ramp.com", "career_url": "https://jobs.ashbyhq.com/ramp"},
        # Lever
        {"name": "Block", "domain": "block.xyz", "career_url": "https://jobs.lever.co/block"},
        {"name": "Plaid", "domain": "plaid.com", "career_url": "https://jobs.lever.co/plaid"},
        {"name": "Blend", "domain": "blend.com", "career_url": "https://jobs.lever.co/blend"},
        # Greenhouse
        {"name": "Robinhood", "domain": "robinhood.com", "career_url": "https://boards.greenhouse.io/robinhood"},
        {"name": "Coinbase", "domain": "coinbase.com", "career_url": "https://boards.greenhouse.io/coinbase"},
        {"name": "Brex", "domain": "brex.com", "career_url": "https://boards.greenhouse.io/brex"},
        {"name": "Affirm", "domain": "affirm.com", "career_url": "https://boards.greenhouse.io/affirm"},
        {"name": "Upstart", "domain": "upstart.com", "career_url": "https://boards.greenhouse.io/upstart"},
        {"name": "Chime", "domain": "chime.com", "career_url": "https://boards.greenhouse.io/chime"},
        {"name": "SoFi", "domain": "sofi.com", "career_url": "https://boards.greenhouse.io/sofi"},
        {"name": "Wealthfront", "domain": "wealthfront.com", "career_url": "https://boards.greenhouse.io/wealthfront"},
        {"name": "Carta", "domain": "carta.com", "career_url": "https://boards.greenhouse.io/carta"},
        {"name": "Marqeta", "domain": "marqeta.com", "career_url": "https://boards.greenhouse.io/marqeta"},
        {"name": "Toast", "domain": "toasttab.com", "career_url": "https://boards.greenhouse.io/toast"},
        {"name": "Addepar", "domain": "addepar.com", "career_url": "https://boards.greenhouse.io/addepar"},
        {"name": "Stash", "domain": "stash.com", "career_url": "https://boards.greenhouse.io/stash"},
        {"name": "Chainalysis", "domain": "chainalysis.com", "career_url": "https://boards.greenhouse.io/chainalysis"},
        {"name": "Ripple", "domain": "ripple.com", "career_url": "https://boards.greenhouse.io/ripple"},
        {"name": "Gemini", "domain": "gemini.com", "career_url": "https://boards.greenhouse.io/gemini"},
        {"name": "Circle", "domain": "circle.com", "career_url": "https://boards.greenhouse.io/circle"},
        {"name": "Apex Fintech", "domain": "apexfintechsolutions.com", "career_url": "https://boards.greenhouse.io/apexfintechsolutions"},
        {"name": "Capital One", "domain": "capitalone.com", "career_url": "https://capitalone.wd1.myworkdayjobs.com/Capital_One"},
        {"name": "Charles Schwab", "domain": "schwab.com", "career_url": "https://schwab.wd5.myworkdayjobs.com/SchwabJobs"},
        {"name": "FIS", "domain": "fisglobal.com", "career_url": "https://fis.wd5.myworkdayjobs.com/FISCareers"},
        {"name": "Fiserv", "domain": "fiserv.com", "career_url": "https://fiserv.wd5.myworkdayjobs.com/EXT"},
        {"name": "S&P Global", "domain": "spglobal.com", "career_url": "https://spglobal.wd5.myworkdayjobs.com/SPGlobal_Careers"},
        {"name": "Northern Trust", "domain": "northerntrust.com", "career_url": "https://northerntrust.wd1.myworkdayjobs.com/NT"},
        {"name": "Discover", "domain": "discover.com", "career_url": "https://discover.wd5.myworkdayjobs.com/Discover_Careers"},
        {"name": "FactSet", "domain": "factset.com", "career_url": "https://factset.wd1.myworkdayjobs.com/FactSet"},
        {"name": "Mercury", "domain": "mercury.com", "career_url": "https://jobs.lever.co/mercury"},
        {"name": "Melio", "domain": "melio.com", "career_url": "https://boards.greenhouse.io/melio"},
        {"name": "Modern Treasury", "domain": "moderntreasury.com", "career_url": "https://jobs.ashbyhq.com/moderntreasury"},
        {"name": "Alloy", "domain": "alloy.com", "career_url": "https://boards.greenhouse.io/alloy"},
        {"name": "TrueNorth", "domain": "truenorth.co", "career_url": "https://boards.greenhouse.io/truenorth"},
    ],
    "Insurance": [
        # Dice ATS Platform
        {"name": "Dice InsurTech", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=insurance+software", "industry": "Insurance"},
        # Workday CXS
        {"name": "Travelers", "domain": "travelers.com", "career_url": "https://travelers.wd5.myworkdayjobs.com/External"},
        # Lever
        {"name": "Coalition", "domain": "coalitioninc.com", "career_url": "https://jobs.lever.co/coalition"},
        {"name": "Cowbell Cyber", "domain": "cowbell.insure", "career_url": "https://jobs.lever.co/cowbellcyber"},
        {"name": "Branch Insurance", "domain": "ourbranch.com", "career_url": "https://jobs.lever.co/ourbranch"},
        # Greenhouse
        {"name": "Lemonade", "domain": "lemonade.com", "career_url": "https://boards.greenhouse.io/lemonade"},
        {"name": "Root Insurance", "domain": "joinroot.com", "career_url": "https://boards.greenhouse.io/joinroot"},
        {"name": "Hippo Insurance", "domain": "hippo.com", "career_url": "https://boards.greenhouse.io/hippo"},
        {"name": "Policygenius", "domain": "policygenius.com", "career_url": "https://boards.greenhouse.io/policygenius"},
        {"name": "Kin Insurance", "domain": "kin.com", "career_url": "https://boards.greenhouse.io/kininsurance"},
        {"name": "Next Insurance", "domain": "nextinsurance.com", "career_url": "https://boards.greenhouse.io/nextinsurance"},
        {"name": "Pie Insurance", "domain": "pieinsurance.com", "career_url": "https://boards.greenhouse.io/pieinsurance"},
        {"name": "Clearcover", "domain": "clearcover.com", "career_url": "https://boards.greenhouse.io/clearcover"},
        {"name": "Ethos Life", "domain": "ethoslife.com", "career_url": "https://boards.greenhouse.io/ethoslife"},
        {"name": "Corvus Insurance", "domain": "corvusinsurance.com", "career_url": "https://boards.greenhouse.io/corvus"},
        {"name": "Openly", "domain": "openly.com", "career_url": "https://boards.greenhouse.io/openly"},
        {"name": "At-Bay", "domain": "at-bay.com", "career_url": "https://boards.greenhouse.io/atbay"},
        {"name": "AgentSync", "domain": "agentsync.io", "career_url": "https://boards.greenhouse.io/agentsync"},
        {"name": "Prudential", "domain": "prudential.com", "career_url": "https://prudential.wd5.myworkdayjobs.com/PrudentialCareers"},
        {"name": "Allstate", "domain": "allstate.com", "career_url": "https://allstate.wd1.myworkdayjobs.com/AllstateCareers"},
        {"name": "Aflac", "domain": "aflac.com", "career_url": "https://aflac.wd1.myworkdayjobs.com/Aflac_Careers"},
        {"name": "MetLife", "domain": "metlife.com", "career_url": "https://metlife.wd1.myworkdayjobs.com/MetLife"},
        {"name": "The Hartford", "domain": "thehartford.com", "career_url": "https://thehartford.wd5.myworkdayjobs.com/The_Hartford_External"},
        {"name": "Lincoln Financial", "domain": "lfg.com", "career_url": "https://lfg.wd5.myworkdayjobs.com/Lincoln_Careers"},
        {"name": "Principal Financial Group", "domain": "principal.com", "career_url": "https://principal.wd1.myworkdayjobs.com/Principal_Careers"},
        {"name": "Markel", "domain": "markel.com", "career_url": "https://markel.wd5.myworkdayjobs.com/Markel_Careers"},
        {"name": "Hanover Insurance", "domain": "hanover.com", "career_url": "https://hanover.wd1.myworkdayjobs.com/Hanover"},
        {"name": "Vouch", "domain": "vouch.us", "career_url": "https://boards.greenhouse.io/vouch"},
        {"name": "Boost Insurance", "domain": "boostinsurance.com", "career_url": "https://boards.greenhouse.io/boostinsurance"},
        {"name": "Newfront", "domain": "newfront.com", "career_url": "https://jobs.ashbyhq.com/newfront"},
    ],
    "Solar, Energy & Utilities": [
        # Dice ATS Platform
        {"name": "Dice CleanTech", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=energy+software", "industry": "Solar, Energy & Utilities"},
        # SmartRecruiters
        {"name": "Schneider Electric", "domain": "se.com", "career_url": "https://jobs.smartrecruiters.com/SchneiderElectric"},
        # Lever
        {"name": "Span", "domain": "span.io", "career_url": "https://jobs.lever.co/span"},
        {"name": "Fluence Energy", "domain": "fluenceenergy.com", "career_url": "https://jobs.lever.co/fluence"},
        {"name": "Crusoe Energy", "domain": "crusoeenergy.com", "career_url": "https://jobs.lever.co/crusoeenergy"},
        {"name": "Ample", "domain": "ample.com", "career_url": "https://jobs.lever.co/ample"},
        {"name": "Electric Hydrogen", "domain": "eh2.com", "career_url": "https://jobs.lever.co/eh2"},
        # Greenhouse
        {"name": "Redwood Materials", "domain": "redwoodmaterials.com", "career_url": "https://boards.greenhouse.io/redwoodmaterials"},
        {"name": "Form Energy", "domain": "formenergy.com", "career_url": "https://boards.greenhouse.io/formenergy"},
        {"name": "Aurora Solar", "domain": "aurorasolar.com", "career_url": "https://boards.greenhouse.io/aurorasolar"},
        {"name": "ChargePoint", "domain": "chargepoint.com", "career_url": "https://boards.greenhouse.io/chargepoint"},
        {"name": "Palmetto", "domain": "palmetto.com", "career_url": "https://boards.greenhouse.io/palmetto"},
        {"name": "Stem Inc", "domain": "stem.com", "career_url": "https://boards.greenhouse.io/steminc"},
        {"name": "Solaria", "domain": "solaria.com", "career_url": "https://boards.greenhouse.io/solaria"},
        {"name": "LevelTen Energy", "domain": "leveltenenergy.com", "career_url": "https://boards.greenhouse.io/leveltenenergy"},
        {"name": "Arcadia", "domain": "arcadia.com", "career_url": "https://boards.greenhouse.io/arcadia"},
        {"name": "Sunnova", "domain": "sunnova.com", "career_url": "https://boards.greenhouse.io/sunnova"},
        {"name": "Nextracker", "domain": "nextracker.com", "career_url": "https://boards.greenhouse.io/nextracker"},
        {"name": "NextEra Energy", "domain": "nexteraenergy.com", "career_url": "https://nexteraenergy.wd5.myworkdayjobs.com/NextEra_Energy"},
        {"name": "Southern Company", "domain": "southerncompany.com", "career_url": "https://southerncompany.wd5.myworkdayjobs.com/Southern_Company_Careers"},
        {"name": "AES Corporation", "domain": "aes.com", "career_url": "https://aes.wd1.myworkdayjobs.com/AES_Careers"},
        {"name": "First Solar", "domain": "firstsolar.com", "career_url": "https://firstsolar.wd1.myworkdayjobs.com/FirstSolarCareers"},
        {"name": "Enphase Energy", "domain": "enphase.com", "career_url": "https://enphase.wd5.myworkdayjobs.com/Enphase_Careers"},
        {"name": "Sunrun", "domain": "sunrun.com", "career_url": "https://sunrun.wd1.myworkdayjobs.com/Sunrun_Careers"},
        {"name": "Constellation Energy", "domain": "constellation.com", "career_url": "https://constellation.wd1.myworkdayjobs.com/Constellation"},
        {"name": "Fervo Energy", "domain": "fervoenergy.com", "career_url": "https://jobs.ashbyhq.com/fervoenergy"},
        {"name": "Commonwealth Fusion Systems", "domain": "cfs.energy", "career_url": "https://jobs.lever.co/cfs"},
        {"name": "Helion Energy", "domain": "helionenergy.com", "career_url": "https://jobs.lever.co/helionenergy"},
        {"name": "Antora Energy", "domain": "antoraenergy.com", "career_url": "https://jobs.lever.co/antoraenergy"},
    ],
    "Aerospace & Defense": [
        # Dice ATS Platform
        {"name": "Dice DefenseTech", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=defense+software", "industry": "Aerospace & Defense"},
        # Workday CXS
        {"name": "Boeing", "domain": "boeing.com", "career_url": "https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS"},
        # Ashby
        {"name": "Apex Space", "domain": "apextechnology.com", "career_url": "https://jobs.ashbyhq.com/apex"},
        # Lever
        {"name": "Anduril Industries", "domain": "anduril.com", "career_url": "https://jobs.lever.co/anduril"},
        {"name": "Astranis", "domain": "astranis.com", "career_url": "https://jobs.lever.co/astranis"},
        {"name": "Shield AI", "domain": "shield.ai", "career_url": "https://jobs.lever.co/shieldai"},
        {"name": "Relativity Space", "domain": "relativityspace.com", "career_url": "https://jobs.lever.co/relativityspace"},
        {"name": "Skydio", "domain": "skydio.com", "career_url": "https://jobs.lever.co/skydio"},
        {"name": "Epirus", "domain": "epirusinc.com", "career_url": "https://jobs.lever.co/epirus"},
        {"name": "Hermeus", "domain": "hermeus.com", "career_url": "https://jobs.lever.co/hermeus"},
        {"name": "Varda Space Industries", "domain": "varda.com", "career_url": "https://jobs.lever.co/varda"},
        {"name": "Joby Aviation", "domain": "jobyaviation.com", "career_url": "https://jobs.lever.co/jobyaviation"},
        {"name": "Stoke Space", "domain": "stokespace.com", "career_url": "https://jobs.lever.co/stokespace"},
        {"name": "Ursa Major", "domain": "ursamajor.com", "career_url": "https://jobs.lever.co/ursamajor"},
        {"name": "Palantir Technologies", "domain": "palantir.com", "career_url": "https://jobs.lever.co/palantir"},
        # Greenhouse
        {"name": "Rocket Lab", "domain": "rocketlabusa.com", "career_url": "https://boards.greenhouse.io/rocketlab"},
        {"name": "Two Six Technologies", "domain": "twosixtech.com", "career_url": "https://boards.greenhouse.io/twosixtechnologies"},
        {"name": "BlackSky Technology", "domain": "blacksky.com", "career_url": "https://boards.greenhouse.io/blacksky"},
        {"name": "Planet Labs", "domain": "planet.com", "career_url": "https://boards.greenhouse.io/planetlabs"},
        {"name": "Archer Aviation", "domain": "archer.com", "career_url": "https://boards.greenhouse.io/archer"},
        {"name": "HawkEye 360", "domain": "he360.com", "career_url": "https://boards.greenhouse.io/hawkeye360"},
        {"name": "SpaceX", "domain": "spacex.com", "career_url": "https://boards.greenhouse.io/spacex"},
        {"name": "Applied Intuition", "domain": "appliedintuition.com", "career_url": "https://boards.greenhouse.io/appliedintuition"},
        {"name": "True Anomaly", "domain": "trueanomaly.com", "career_url": "https://boards.greenhouse.io/trueanomaly"},
        {"name": "Lockheed Martin", "domain": "lockheedmartin.com", "career_url": "https://lockheedmartin.wd5.myworkdayjobs.com/Lockheed_Martin_Careers"},
        {"name": "Northrop Grumman", "domain": "northropgrumman.com", "career_url": "https://northropgrumman.wd1.myworkdayjobs.com/NG_Careers"},
        {"name": "RTX", "domain": "rtx.com", "career_url": "https://rtx.wd1.myworkdayjobs.com/en-US/RTX_Careers"},
        {"name": "General Dynamics", "domain": "generaldynamics.com", "career_url": "https://generaldynamics.wd1.myworkdayjobs.com/GD_Careers"},
        {"name": "L3Harris", "domain": "l3harris.com", "career_url": "https://l3harris.wd1.myworkdayjobs.com/L3Harris_Careers"},
        {"name": "Leidos", "domain": "leidos.com", "career_url": "https://leidos.wd5.myworkdayjobs.com/External"},
        {"name": "Textron", "domain": "textron.com", "career_url": "https://textron.wd1.myworkdayjobs.com/Textron_Careers"},
        {"name": "Huntington Ingalls", "domain": "huntingtoningalls.com", "career_url": "https://hii.wd1.myworkdayjobs.com/HII_Careers"},
        {"name": "Curtiss-Wright", "domain": "curtisswright.com", "career_url": "https://curtisswright.wd1.myworkdayjobs.com/CW_Careers"},
        {"name": "Firefly Aerospace", "domain": "fireflyspace.com", "career_url": "https://boards.greenhouse.io/fireflyaerospace"},
        {"name": "Impulse Space", "domain": "impulsespace.com", "career_url": "https://jobs.ashbyhq.com/impulsespace"},
        {"name": "Hadrian", "domain": "hadrian.co", "career_url": "https://jobs.ashbyhq.com/hadrian"},
        {"name": "Saronic", "domain": "saronic.com", "career_url": "https://jobs.ashbyhq.com/saronic"},
        {"name": "Sierra Space", "domain": "sierraspace.com", "career_url": "https://jobs.lever.co/sierraspace"},
    ],
    "Pharma & Biotechnology": [
        # Dice ATS Platform
        {"name": "Dice BioTech", "domain": "dice.com", "career_url": "https://www.dice.com/jobs?q=bioinformatics", "industry": "Pharma & Biotechnology"},
        # Workday CXS
        {"name": "Amgen", "domain": "amgen.com", "career_url": "https://amgen.wd1.myworkdayjobs.com/Careers"},
        {"name": "Pfizer", "domain": "pfizer.com", "career_url": "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"},
        {"name": "Gilead Sciences", "domain": "gilead.com", "career_url": "https://gilead.wd1.myworkdayjobs.com/gileadcareers"},
        {"name": "Illumina", "domain": "illumina.com", "career_url": "https://illumina.wd1.myworkdayjobs.com/illumina-careers"},
        # Lever
        {"name": "Insitro", "domain": "insitro.com", "career_url": "https://jobs.lever.co/insitro"},
        {"name": "Altos Labs", "domain": "altoslabs.com", "career_url": "https://jobs.lever.co/altoslabs"},
        {"name": "Arsenal Biosciences", "domain": "arsenalbio.com", "career_url": "https://jobs.lever.co/arsenalbio"},
        {"name": "Graphite Bio", "domain": "graphitebio.com", "career_url": "https://jobs.lever.co/graphitebio"},
        # Greenhouse
        {"name": "Ginkgo Bioworks", "domain": "ginkgobioworks.com", "career_url": "https://boards.greenhouse.io/ginkgobioworks"},
        {"name": "Twist Bioscience", "domain": "twistbioscience.com", "career_url": "https://boards.greenhouse.io/twistbioscience"},
        {"name": "Prime Medicine", "domain": "primemedicine.com", "career_url": "https://boards.greenhouse.io/primemedicine"},
        {"name": "Beam Therapeutics", "domain": "beamtx.com", "career_url": "https://boards.greenhouse.io/beamtherapeutics"},
        {"name": "Recursion Pharmaceuticals", "domain": "recursion.com", "career_url": "https://boards.greenhouse.io/recursionpharma"},
        {"name": "Tempus AI", "domain": "tempus.com", "career_url": "https://boards.greenhouse.io/tempus"},
        {"name": "Resilience", "domain": "resilience.com", "career_url": "https://boards.greenhouse.io/resilience"},
        {"name": "10x Genomics", "domain": "10xgenomics.com", "career_url": "https://boards.greenhouse.io/10xgenomics"},
        {"name": "Mammoth Biosciences", "domain": "mammoth.bio", "career_url": "https://boards.greenhouse.io/mammothbiosci"},
        {"name": "Sana Biotechnology", "domain": "sana.com", "career_url": "https://boards.greenhouse.io/sanabiotechnology"},
        {"name": "Relay Therapeutics", "domain": "relaytx.com", "career_url": "https://boards.greenhouse.io/relaytx"},
        {"name": "Generate:Biomedicines", "domain": "generatebiomedicines.com", "career_url": "https://boards.greenhouse.io/generatebiomedicines"},
        {"name": "Benchling", "domain": "benchling.com", "career_url": "https://boards.greenhouse.io/benchling"},
        {"name": "Schrödinger", "domain": "schrodinger.com", "career_url": "https://boards.greenhouse.io/schrodinger"},
        {"name": "Verve Therapeutics", "domain": "vervetx.com", "career_url": "https://boards.greenhouse.io/vervetx"},
        {"name": "Johnson & Johnson", "domain": "jnj.com", "career_url": "https://jnj.wd5.myworkdayjobs.com/JNJ_Careers"},
        {"name": "Merck", "domain": "merck.com", "career_url": "https://merck.wd5.myworkdayjobs.com/MerckCareers"},
        {"name": "Bristol Myers Squibb", "domain": "bms.com", "career_url": "https://bms.wd5.myworkdayjobs.com/BMS"},
        {"name": "Eli Lilly", "domain": "lilly.com", "career_url": "https://lilly.wd5.myworkdayjobs.com/Lilly_Careers"},
        {"name": "AbbVie", "domain": "abbvie.com", "career_url": "https://abbvie.wd1.myworkdayjobs.com/AbbVieCareers"},
        {"name": "Regeneron", "domain": "regeneron.com", "career_url": "https://regeneron.wd1.myworkdayjobs.com/RegeneronCareers"},
        {"name": "Biogen", "domain": "biogen.com", "career_url": "https://biogen.wd1.myworkdayjobs.com/Biogen_Careers"},
        {"name": "Vertex Pharmaceuticals", "domain": "vrtx.com", "career_url": "https://vertex.wd1.myworkdayjobs.com/VertexCareers"},
        {"name": "Bio-Rad Laboratories", "domain": "bio-rad.com", "career_url": "https://biorad.wd5.myworkdayjobs.com/BioRad_Careers"},
        {"name": "Moderna", "domain": "modernatx.com", "career_url": "https://moderna.wd1.myworkdayjobs.com/ModernaCareers"},
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
        self, industry: str, company_filter: Optional[str] = None, ats_filter: Optional[str] = None
    ) -> List[Tuple[Company, JobSource]]:
        """
        Flow Step 3: Find Companies in Industry.
        Retrieves companies belonging to the identified industry, along with their active career page sources.
        Automatically registers verified companies into PostgreSQL on-the-fly without needing seed_data.sql.
        Filters by ATS platform if ats_filter is specified.
        """
        ind_clean = normalize_industry_name(industry)

        # 1. Ensure all verified high-yield companies for this industry are registered and active in PostgreSQL
        if ind_clean in VERIFIED_INDUSTRY_COMPANIES:
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

        # 2. Retrieve matched companies from the database
        matched_companies: List[Company] = []
        if company_filter:
            comp = self.repo.get_company_by_name(company_filter)
            if comp:
                matched_companies.append(comp)
        else:
            matched_companies = self.repo.get_companies_by_industry(ind_clean)

        # 3. Build (Company, JobSource) pairs and prioritize high-yield ATS sources first
        verified_names = {c["name"].lower() for c in VERIFIED_INDUSTRY_COMPANIES.get(ind_clean, [])}
        verified_results: List[Tuple[Company, JobSource]] = []
        other_results: List[Tuple[Company, JobSource]] = []

        for comp in matched_companies:
            sources = self.repo.get_active_sources_for_company(comp.id)
            pair = None
            for src in sources:
                if src.scraper_type == "playwright" or "career" in src.source_url or "job" in src.source_url:
                    pair = (comp, src)
                    break
            else:
                if comp.career_url:
                    src = self.repo.get_or_create_job_source(
                        company_id=comp.id,
                        source_url=comp.career_url,
                        scraper_type="playwright",
                    )
                    pair = (comp, src)

            if pair:
                if ats_filter and ats_filter.upper() != "ALL":
                    if not matches_ats(pair[1].source_url, ats_filter):
                        continue

                if comp.name.lower() in verified_names or any(ats in pair[1].source_url for ats in [
                    "greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com",
                    "smartrecruiters.com", "bamboohr.com", "jobvite.com", "icims.com", "taleo.net",
                    "dice.com"
                ]):
                    verified_results.append(pair)
                else:
                    other_results.append(pair)

        # Prioritize verified high-yield ATS boards first, followed by others
        return verified_results + other_results

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
