import urllib.request
import re

def check_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            # Check for error indicators
            for err in ["sorry, but we can't find that page", "page not found", "job is no longer available", "posting has expired"]:
                if err in content.lower():
                    return False, f"Error text: {err}"
            return True, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

test_urls = [
    "https://boards.greenhouse.io/company/careers/engineering/senior-manager-infrastructure-data-science-7641390002",
    "https://www.databricks.com/company/careers/engineering/senior-manager-infrastructure-data-science-7641390002",
    "https://boards.greenhouse.io/databricks/jobs/7641390002",
    "https://www.samsara.com/company/careers/roles/8179593?gh_jid=8179593&gh_board=samsara",
    "https://boards.greenhouse.io/samsara/jobs/8179593"
]

for u in test_urls:
    active, reason = check_url(u)
    print(f"URL: {u}\n  Active: {active} ({reason})\n")

