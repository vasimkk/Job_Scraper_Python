import urllib.request
import json

gh_companies = [
    ("Lemonade", "lemonade"),
    ("Root Insurance", "joinroot"),
    ("Hippo", "hippo"),
    ("Policygenius", "policygenius"),
    ("Kin Insurance", "kininsurance"),
    ("Next Insurance", "nextinsurance"),
    ("Clearcover", "clearcover"),
    ("Corvus", "corvus"),
    ("Openly", "openly"),
    ("At-Bay", "atbay"),
    ("AgentSync", "agentsync"),
    ("Form Energy", "formenergy"),
    ("ChargePoint", "chargepoint"),
    ("Palmetto", "palmetto"),
    ("Stem Inc", "steminc"),
    ("Arcadia", "arcadia"),
    ("Sunnova", "sunnova"),
    ("Nextracker", "nextracker"),
    ("Archer Aviation", "archer"),
    ("Applied Intuition", "appliedintuition"),
    ("True Anomaly", "trueanomaly"),
    ("Recursion Pharma", "recursionpharma"),
    ("Resilience", "resilience"),
    ("10x Genomics", "10xgenomics"),
    ("Mammoth Biosciences", "mammothbiosci"),
    ("Sana Biotechnology", "sanabiotechnology"),
    ("Relay Therapeutics", "relaytx"),
    ("Marqeta", "marqeta"),
    ("Addepar", "addepar"),
    ("Stash", "stash"),
    ("Chainalysis", "chainalysis"),
    ("Circle", "circle"),
    ("Apex Fintech", "apexfintechsolutions"),
    ("Tempus AI", "tempus"),
    ("Ro", "ro"),
    ("Datavant", "datavant"),
    ("GoodRx", "goodrx"),
    ("Hinge Health", "hingehealth"),
    ("Cedar", "cedar"),
    ("Lyra Health", "lyrahealth"),
    ("SonderMind", "sondermind"),
    ("Wheel", "wheel"),
]

total_jobs = 0
for name, slug in gh_companies:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            jobs = data.get("jobs", [])
            print(f"{name} ({slug}): {len(jobs)} jobs")
            total_jobs += len(jobs)
    except Exception as e:
        print(f"Error {name}: {e}")

print(f"\nTotal potential Greenhouse jobs from these {len(gh_companies)} companies: {total_jobs}")

