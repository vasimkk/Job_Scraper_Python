import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor

COMPANIES_TO_TEST = [
    # Insurance
    ("Lemonade", "https://boards-api.greenhouse.io/v1/boards/lemonade/jobs", "https://boards.greenhouse.io/lemonade", "Insurance"),
    ("Next Insurance", "https://boards-api.greenhouse.io/v1/boards/nextinsurance/jobs", "https://boards.greenhouse.io/nextinsurance", "Insurance"),
    ("Newfront", "https://boards-api.greenhouse.io/v1/boards/newfront/jobs", "https://boards.greenhouse.io/newfront", "Insurance"),
    ("At-Bay", "https://boards-api.greenhouse.io/v1/boards/atbay/jobs", "https://boards.greenhouse.io/atbay", "Insurance"),
    ("Corvus", "https://boards-api.greenhouse.io/v1/boards/corvusinsurance/jobs", "https://boards.greenhouse.io/corvusinsurance", "Insurance"),
    ("Openly", "https://boards-api.greenhouse.io/v1/boards/openly/jobs", "https://boards.greenhouse.io/openly", "Insurance"),
    ("AgentSync", "https://boards-api.greenhouse.io/v1/boards/agentsync/jobs", "https://boards.greenhouse.io/agentsync", "Insurance"),

    # Healthcare
    ("Tempus AI", "https://boards-api.greenhouse.io/v1/boards/tempus/jobs", "https://boards.greenhouse.io/tempus", "Healthcare"),
    ("Flatiron Health", "https://boards-api.greenhouse.io/v1/boards/flatiron/jobs", "https://boards.greenhouse.io/flatiron", "Healthcare"),
    ("Hims & Hers", "https://boards-api.greenhouse.io/v1/boards/forhims/jobs", "https://boards.greenhouse.io/forhims", "Healthcare"),
    ("Lyra Health", "https://boards-api.greenhouse.io/v1/boards/lyrahealth/jobs", "https://boards.greenhouse.io/lyrahealth", "Healthcare"),
    ("Cityblock Health", "https://boards-api.greenhouse.io/v1/boards/cityblock/jobs", "https://boards.greenhouse.io/cityblock", "Healthcare"),
    ("Spring Health", "https://boards-api.greenhouse.io/v1/boards/springhealth/jobs", "https://boards.greenhouse.io/springhealth", "Healthcare"),
    ("Cedar", "https://boards-api.greenhouse.io/v1/boards/cedar/jobs", "https://boards.greenhouse.io/cedar", "Healthcare"),
    ("Aledade", "https://boards-api.greenhouse.io/v1/boards/aledade/jobs", "https://boards.greenhouse.io/aledade", "Healthcare"),

    # Solar, Energy & Utilities
    ("Fluence Energy", "https://boards-api.greenhouse.io/v1/boards/fluenceenergy/jobs", "https://boards.greenhouse.io/fluenceenergy", "Solar, Energy & Utilities"),
    ("Generate Capital", "https://boards-api.greenhouse.io/v1/boards/generatecapital/jobs", "https://boards.greenhouse.io/generatecapital", "Solar, Energy & Utilities"),
    ("CleanChoice Energy", "https://boards-api.greenhouse.io/v1/boards/cleanchoiceenergy/jobs", "https://boards.greenhouse.io/cleanchoiceenergy", "Solar, Energy & Utilities"),
    ("Stem Inc", "https://boards-api.greenhouse.io/v1/boards/stem/jobs", "https://boards.greenhouse.io/stem", "Solar, Energy & Utilities"),

    # Aerospace & Defense
    ("Shield AI", "https://boards-api.greenhouse.io/v1/boards/shieldai/jobs", "https://boards.greenhouse.io/shieldai", "Aerospace & Defense"),
    ("Skydio", "https://boards-api.greenhouse.io/v1/boards/skydio/jobs", "https://boards.greenhouse.io/skydio", "Aerospace & Defense"),
    ("Joby Aviation", "https://boards-api.greenhouse.io/v1/boards/jobyaviation/jobs", "https://boards.greenhouse.io/jobyaviation", "Aerospace & Defense"),
    ("Hermeus", "https://boards-api.greenhouse.io/v1/boards/hermeus/jobs", "https://boards.greenhouse.io/hermeus", "Aerospace & Defense"),
    ("Varda Space", "https://boards-api.greenhouse.io/v1/boards/vardaspaceindustries/jobs", "https://boards.greenhouse.io/vardaspaceindustries", "Aerospace & Defense"),

    # Pharma & Biotechnology
    ("Insitro", "https://boards-api.greenhouse.io/v1/boards/insitro/jobs", "https://boards.greenhouse.io/insitro", "Pharma & Biotechnology"),
    ("10x Genomics", "https://boards-api.greenhouse.io/v1/boards/10xgenomics/jobs", "https://boards.greenhouse.io/10xgenomics", "Pharma & Biotechnology"),
    ("Mammoth Biosciences", "https://boards-api.greenhouse.io/v1/boards/mammothbiosciences/jobs", "https://boards.greenhouse.io/mammothbiosciences", "Pharma & Biotechnology"),
    ("Sana Biotechnology", "https://boards-api.greenhouse.io/v1/boards/sanabiotechnology/jobs", "https://boards.greenhouse.io/sanabiotechnology", "Pharma & Biotechnology"),
    ("Editas Medicine", "https://boards-api.greenhouse.io/v1/boards/editasmedicine/jobs", "https://boards.greenhouse.io/editasmedicine", "Pharma & Biotechnology"),

    # IT, Software & Technology
    ("GitLab", "https://boards-api.greenhouse.io/v1/boards/gitlab/jobs", "https://boards.greenhouse.io/gitlab", "IT, Software & Technology"),
    ("Docker", "https://boards-api.greenhouse.io/v1/boards/docker/jobs", "https://boards.greenhouse.io/docker", "IT, Software & Technology"),
    ("Okta", "https://boards-api.greenhouse.io/v1/boards/okta/jobs", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    ("Twilio", "https://boards-api.greenhouse.io/v1/boards/twilio/jobs", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("Databricks", "https://boards-api.greenhouse.io/v1/boards/databricks/jobs", "https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    ("MongoDB", "https://boards-api.greenhouse.io/v1/boards/mongodb/jobs", "https://boards.greenhouse.io/mongodb", "IT, Software & Technology"),
]

def check(item):
    name, api_url, page_url, industry = item
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            cnt = len(data.get("jobs", []))
            if cnt > 0:
                return (name, page_url, industry, cnt)
    except Exception:
        pass
    return None

with ThreadPoolExecutor(max_workers=15) as executor:
    results = list(executor.map(check, COMPANIES_TO_TEST))

valid = [r for r in results if r]
print(f"Found {len(valid)} verified high-yield active companies:")
for name, page_url, ind, cnt in sorted(valid, key=lambda x: (x[2], -x[3])):
    print(f"  [{ind}] {name}: {cnt} jobs -> {page_url}")

