import sys
sys.path.insert(0, ".")
import urllib.request
import json
from scraper_agent.config import SCRAPER_CONFIG

def check_wd(name, host, tenant, board):
    url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
    payload = json.dumps({"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            total = data.get("total", 0)
            if total > 0:
                print(f"[SUCCESS] {name}: {total} jobs ({host}/{board})")
                return total
            else:
                print(f"[ZERO] {name}: total=0")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
    return 0

candidates = [
    # IT, Software & Tech
    ("NVIDIA", "nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite"),
    ("Adobe", "adobe.wd5.myworkdayjobs.com", "adobe", "external_experienced"),
    ("Salesforce", "salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site"),
    ("Workday", "workday.wd5.myworkdayjobs.com", "workday", "Workday"),
    ("Autodesk", "autodesk.wd1.myworkdayjobs.com", "autodesk", "Ext"),
    ("ServiceNow", "careers.servicenow.com", "servicenow", "careers"),
    ("Intuit", "intuit.wd5.myworkdayjobs.com", "intuit", "External"),
    ("Qualcomm", "qualcomm.wd5.myworkdayjobs.com", "qualcomm", "External"),
    ("AMD", "amd.wd1.myworkdayjobs.com", "amd", "AMD_External_Careers"),
    ("Broadcom", "broadcom.wd1.myworkdayjobs.com", "broadcom", "External_Career"),

    # Healthcare
    ("Humana", "humana.wd5.myworkdayjobs.com", "humana", "Humana_External_Career_Site"),
    ("Medtronic", "medtronic.wd1.myworkdayjobs.com", "medtronic", "MedtronicCareers"),
    ("Boston Scientific", "bostonscientific.wd5.myworkdayjobs.com", "bostonscientific", "bsc_careers"),
    ("Stryker", "stryker.wd1.myworkdayjobs.com", "stryker", "StrykerCareers"),
    ("Danaher", "danaher.wd1.myworkdayjobs.com", "danaher", "DanaherJobs"),
    ("Baxter", "baxter.wd1.myworkdayjobs.com", "baxter", "BaxterCareers"),
    ("Becton Dickinson", "bd.wd1.myworkdayjobs.com", "bd", "External_Career_Site"),
    ("Tenet Healthcare", "tenet.wd1.myworkdayjobs.com", "tenet", "Tenet_Careers"),

    # Pharma & Biotech
    ("Pfizer", "pfizer.wd1.myworkdayjobs.com", "pfizer", "PfizerCareers"),
    ("Amgen", "amgen.wd1.myworkdayjobs.com", "amgen", "Careers"),
    ("Gilead Sciences", "gilead.wd1.myworkdayjobs.com", "gilead", "gileadcareers"),
    ("Bristol Myers Squibb", "bms.wd5.myworkdayjobs.com", "bms", "BMSRadicalCareers"),
    ("Biogen", "biogen.wd1.myworkdayjobs.com", "biogen", "External"),
    ("Vertex", "vrtx.wd5.myworkdayjobs.com", "vrtx", "vertex_careers"),
    ("Illumina", "illumina.wd1.myworkdayjobs.com", "illumina", "illumina-careers"),

    # Aerospace & Defense
    ("Boeing", "boeing.wd1.myworkdayjobs.com", "boeing", "EXTERNAL_CAREERS"),
    ("Lockheed Martin", "lockheedmartin.wd5.myworkdayjobs.com", "lockheedmartin", "External"),
    ("General Dynamics", "generaldynamics.wd5.myworkdayjobs.com", "generaldynamics", "GD_Careers"),
    ("L3Harris", "l3harris.wd1.myworkdayjobs.com", "l3harris", "L3Harris_Careers"),
    ("Raytheon (RTX)", "rtx.wd1.myworkdayjobs.com", "rtx", "RTX_Careers"),

    # Insurance
    ("Travelers", "travelers.wd5.myworkdayjobs.com", "travelers", "External"),
    ("Progressive", "progressive.wd5.myworkdayjobs.com", "progressive", "ProgressiveCareers"),
    ("MetLife", "metlife.wd1.myworkdayjobs.com", "metlife", "MetLife_External_Careers"),
    ("Allstate", "allstate.wd1.myworkdayjobs.com", "allstate", "External"),
    ("Chubb", "chubb.wd1.myworkdayjobs.com", "chubb", "chubbcareers"),
    ("Aflac", "aflac.wd1.myworkdayjobs.com", "aflac", "Aflac_External"),

    # Solar, Energy & Utilities
    ("NextEra Energy", "nexteraenergy.wd5.myworkdayjobs.com", "nexteraenergy", "search"),
    ("Duke Energy", "dukeenergy.wd1.myworkdayjobs.com", "dukeenergy", "Duke_Energy_External_Careers"),
    ("Southern Company", "southerncompany.wd5.myworkdayjobs.com", "southerncompany", "Southern_Company_Careers"),
    ("Constellation", "constellation.wd1.myworkdayjobs.com", "constellation", "External"),
    ("AES", "aes.wd1.myworkdayjobs.com", "aes", "AES_Careers"),

    # Finance & Banking
    ("Morgan Stanley", "morganstanley.wd5.myworkdayjobs.com", "morganstanley", "MS_Careers"),
    ("American Express", "aexp.wd1.myworkdayjobs.com", "aexp", "Amex_Careers"),
    ("Charles Schwab", "schwab.wd5.myworkdayjobs.com", "schwab", "External"),
    ("State Street", "statestreet.wd1.myworkdayjobs.com", "statestreet", "GlobalJobSite"),
    ("US Bank", "usbank.wd1.myworkdayjobs.com", "usbank", "US_Bank_Careers"),
]

total_found = 0
for name, host, tenant, board in candidates:
    total_found += check_wd(name, host, tenant, board)

print(f"\nTotal potential Workday jobs found: {total_found}")

