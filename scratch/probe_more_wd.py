import urllib.request
import json

candidates = [
    # Solar, Energy & Utilities
    ("NextEra Energy", "nexteraenergy.wd5.myworkdayjobs.com", "nexteraenergy", ["search", "NextEra_Energy_External_Career_Site", "careers", "External"]),
    ("Duke Energy", "dukeenergy.wd1.myworkdayjobs.com", "dukeenergy", ["Duke_Energy_External_Careers", "duke_energy_careers", "careers", "search"]),
    ("First Solar", "firstsolar.wd1.myworkdayjobs.com", "firstsolar", ["First_Solar_External_Career_Site", "careers", "search"]),
    ("Enphase Energy", "enphase.wd1.myworkdayjobs.com", "enphase", ["enphase_careers", "careers", "search", "External"]),
    ("Sunrun", "sunrun.wd1.myworkdayjobs.com", "sunrun", ["Sunrun_Jobs", "careers", "search"]),
    ("Southern Company", "southerncompany.wd5.myworkdayjobs.com", "southerncompany", ["Southern_Company_Careers", "careers"]),
    ("Constellation Energy", "constellation.wd1.myworkdayjobs.com", "constellation", ["External", "careers"]),
    ("Exelon", "exelon.wd1.myworkdayjobs.com", "exelon", ["careers", "Exelon_External_Career_Site", "External"]),
    ("Eversource", "eversource.wd1.myworkdayjobs.com", "eversource", ["External", "careers"]),

    # Insurance
    ("Allstate", "allstate.wd1.myworkdayjobs.com", "allstate", ["Allstate_External_Career_Site", "External", "careers"]),
    ("Progressive", "progressive.wd5.myworkdayjobs.com", "progressive", ["ProgressiveCareers", "External", "careers"]),
    ("MetLife", "metlife.wd1.myworkdayjobs.com", "metlife", ["MetLife_External_Careers", "careers"]),
    ("Prudential", "prudential.wd5.myworkdayjobs.com", "prudential", ["Prudential_Careers", "careers", "External"]),
    ("Chubb", "chubb.wd1.myworkdayjobs.com", "chubb", ["chubbcareers", "External", "careers"]),
    ("Hartford", "thehartford.wd5.myworkdayjobs.com", "thehartford", ["External", "careers"]),

    # Finance & Banking
    ("Capital One", "capitalone.wd1.myworkdayjobs.com", "capitalone", ["Capital_One", "careers", "External"]),
    ("Fidelity", "fidelity.wd1.myworkdayjobs.com", "fidelity", ["FidelityCareers", "careers", "External"]),
    ("Charles Schwab", "schwab.wd5.myworkdayjobs.com", "schwab", ["Schwab_Jobs", "careers", "External"]),
    ("KeyBank", "keybank.wd5.myworkdayjobs.com", "keybank", ["KeyBank_External_Career_Site", "careers", "External"]),
    ("PNC", "pnc.wd5.myworkdayjobs.com", "pnc", ["PNC_Careers", "External", "careers"]),
    ("State Street", "statestreet.wd1.myworkdayjobs.com", "statestreet", ["GlobalJobSite", "State_Street_Careers", "careers"]),
]

def check(name, host, tenant, board):
    url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
    payload = json.dumps({"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            total = data.get("total", 0)
            if total > 0:
                print(f"FOUND: {name} -> {host}/{board}: {total} jobs")
                return True
    except Exception:
        pass
    return False

for name, host, tenant, boards in candidates:
    for b in boards:
        if check(name, host, tenant, b):
            break

