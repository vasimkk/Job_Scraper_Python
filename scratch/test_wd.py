import sys
sys.path.insert(0, ".")
import urllib.request
import json
from scraper_agent.config import SCRAPER_CONFIG

def check_wd(host, tenant, board):
    url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
    payload = json.dumps({"appliedFacets": {}, "limit": 3, "offset": 0, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": SCRAPER_CONFIG.user_agent, "Accept": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            total = data.get("total", 0)
            print(f"SUCCESS {host}/{tenant}/{board}: total={total}")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} for {host}/{tenant}/{board}")
    except Exception as e:
        print(f"ERROR {host}/{tenant}/{board}: {e}")
    return False

check_wd("davita.wd1.myworkdayjobs.com", "davita", "DaVita_Careers")
check_wd("davita.wd1.myworkdayjobs.com", "davita", "careers")
check_wd("salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site")
check_wd("salesforce.wd1.myworkdayjobs.com", "salesforce", "External_Career_Site")
check_wd("questdiagnostics.wd1.myworkdayjobs.com", "questdiagnostics", "Quest_Careers")
check_wd("capitalone.wd1.myworkdayjobs.com", "capitalone", "Capital_One")
check_wd("fidelity.wd1.myworkdayjobs.com", "fidelity", "FidelityCareers")
