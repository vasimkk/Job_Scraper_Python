import requests

test_boards = [
    # IT
    ("Databricks", "https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    ("Docker", "https://jobs.lever.co/docker", "IT, Software & Technology"),
    ("Fastly", "https://boards.greenhouse.io/fastly", "IT, Software & Technology"),
    ("Twilio", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("MongoDB", "https://boards.greenhouse.io/mongodb", "IT, Software & Technology"),
    ("Okta", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    
    # Healthcare
    ("Ro", "https://boards.greenhouse.io/ro", "Healthcare"),
    ("GoodRx", "https://boards.greenhouse.io/goodrx", "Healthcare"),
    ("Maven Clinic", "https://jobs.lever.co/mavenclinic", "Healthcare"),
    ("Flatiron Health", "https://boards.greenhouse.io/flatiron", "Healthcare"),
    ("HealthVerity", "https://boards.greenhouse.io/healthverity", "Healthcare"),
    ("Cityblock Health", "https://boards.greenhouse.io/cityblockhealth", "Healthcare"),
    
    # Finance
    ("Ramp", "https://jobs.ashbyhq.com/ramp", "Finance & Banking"),
    ("Carta", "https://boards.greenhouse.io/carta", "Finance & Banking"),
    ("Blend", "https://boards.greenhouse.io/blend", "Finance & Banking"),
    ("Wealthfront", "https://boards.greenhouse.io/wealthfront", "Finance & Banking"),
    
    # Insurance
    ("Lemonade", "https://boards.greenhouse.io/lemonade", "Insurance"),
    ("Next Insurance", "https://boards.greenhouse.io/nextinsurance", "Insurance"),
    ("Policygenius", "https://boards.greenhouse.io/policygenius", "Insurance"),
    ("Root Insurance", "https://boards.greenhouse.io/rootinsurance", "Insurance"),
    ("Kin Insurance", "https://boards.greenhouse.io/kininsurance", "Insurance"),
    
    # Energy
    ("Rivian", "https://boards.greenhouse.io/rivian", "Solar, Energy & Utilities"),
    ("Enphase Energy", "https://boards.greenhouse.io/enphase", "Solar, Energy & Utilities"),
    ("Aurora Solar", "https://boards.greenhouse.io/aurorasolar", "Solar, Energy & Utilities"),
    ("Arcadia Power", "https://boards.greenhouse.io/arcadia", "Solar, Energy & Utilities"),
    
    # Aerospace
    ("Relativity Space", "https://boards.greenhouse.io/relativity", "Aerospace & Defense"),
    ("Planet Labs", "https://boards.greenhouse.io/planetlabs", "Aerospace & Defense"),
    ("Sierra Space", "https://boards.greenhouse.io/sierraspace", "Aerospace & Defense"),
    ("Shield AI", "https://boards.greenhouse.io/shieldai", "Aerospace & Defense"),
    ("Joby Aviation", "https://boards.greenhouse.io/jobyaviation", "Aerospace & Defense"),
    
    # Pharma
    ("Moderna", "https://boards.greenhouse.io/moderna", "Pharma & Biotechnology"),
    ("Tempus AI", "https://boards.greenhouse.io/tempus", "Pharma & Biotechnology"),
    ("Twist Bioscience", "https://boards.greenhouse.io/twistbioscience", "Pharma & Biotechnology"),
    ("Alnylam Pharmaceuticals", "https://boards.greenhouse.io/alnylam", "Pharma & Biotechnology"),
    ("Recursion Pharmaceuticals", "https://boards.greenhouse.io/recursion", "Pharma & Biotechnology"),
]

valid_boards = []
for name, url, ind in test_boards:
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.text) > 15000:
            print(f"VALID: {name} ({ind}) -> Length: {len(r.text)}")
            valid_boards.append((name, url, ind))
        else:
            print(f"SKIP ({r.status_code}): {name} -> Length: {len(r.text)}")
    except Exception as e:
        print(f"ERR: {name} -> {e}")

print(f"\nTotal Valid High-Yield Boards: {len(valid_boards)}")

