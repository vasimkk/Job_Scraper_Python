import requests

candidate_companies = [
    # 1. IT, Software & Technology
    ("Databricks", "https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    ("Fastly", "https://boards.greenhouse.io/fastly", "IT, Software & Technology"),
    ("Twilio", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("MongoDB", "https://boards.greenhouse.io/mongodb", "IT, Software & Technology"),
    ("Okta", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    ("Gusto", "https://boards.greenhouse.io/gusto", "IT, Software & Technology"),
    ("Figma", "https://boards.greenhouse.io/figma", "IT, Software & Technology"),
    ("Cloudflare", "https://boards.greenhouse.io/cloudflare", "IT, Software & Technology"),
    ("Datadog", "https://boards.greenhouse.io/datadog", "IT, Software & Technology"),
    ("Supabase", "https://boards.greenhouse.io/supabase", "IT, Software & Technology"),
    ("Notion", "https://boards.greenhouse.io/notion", "IT, Software & Technology"),
    ("Elastic", "https://boards.greenhouse.io/elastic", "IT, Software & Technology"),
    ("Vercel", "https://boards.greenhouse.io/vercel", "IT, Software & Technology"),
    ("Linear", "https://jobs.ashbyhq.com/linear", "IT, Software & Technology"),
    ("Retool", "https://jobs.ashbyhq.com/retool", "IT, Software & Technology"),
    ("Braze", "https://boards.greenhouse.io/braze", "IT, Software & Technology"),
    ("Confluent", "https://boards.greenhouse.io/confluent", "IT, Software & Technology"),
    ("Cockroach Labs", "https://boards.greenhouse.io/cockroachlabs", "IT, Software & Technology"),
    ("HashiCorp", "https://boards.greenhouse.io/hashicorp", "IT, Software & Technology"),

    # 2. Healthcare
    ("Oscar Health", "https://boards.greenhouse.io/oscar", "Healthcare"),
    ("Headway", "https://jobs.ashbyhq.com/headway", "Healthcare"),
    ("HealthVerity", "https://boards.greenhouse.io/healthverity", "Healthcare"),
    ("Komodo Health", "https://boards.greenhouse.io/komodohealth", "Healthcare"),
    ("Doximity", "https://boards.greenhouse.io/doximity", "Healthcare"),
    ("BetterHelp", "https://boards.greenhouse.io/betterhelp", "Healthcare"),
    ("Wheel", "https://boards.greenhouse.io/wheel", "Healthcare"),
    ("Lyra Health", "https://boards.greenhouse.io/lyrahealth", "Healthcare"),
    ("Hims & Hers", "https://boards.greenhouse.io/forhims", "Healthcare"),
    ("Cedar", "https://boards.greenhouse.io/cedar", "Healthcare"),

    # 3. Finance & Banking
    ("Brex", "https://boards.greenhouse.io/brex", "Finance & Banking"),
    ("Ramp", "https://jobs.ashbyhq.com/ramp", "Finance & Banking"),
    ("Carta", "https://boards.greenhouse.io/carta", "Finance & Banking"),
    ("Blend", "https://boards.greenhouse.io/blend", "Finance & Banking"),
    ("Robinhood", "https://boards.greenhouse.io/robinhood", "Finance & Banking"),
    ("Wealthfront", "https://boards.greenhouse.io/wealthfront", "Finance & Banking"),
    ("Affirm", "https://boards.greenhouse.io/affirm", "Finance & Banking"),
    ("Marqeta", "https://boards.greenhouse.io/marqeta", "Finance & Banking"),
    ("Stripe", "https://boards.greenhouse.io/stripe", "Finance & Banking"),

    # 4. Insurance
    ("Coalition", "https://boards.greenhouse.io/coalition", "Insurance"),
    ("Cowbell Cyber", "https://boards.greenhouse.io/cowbellcyber", "Insurance"),
    ("Pie Insurance", "https://boards.greenhouse.io/pieinsurance", "Insurance"),
    ("Clearcover", "https://boards.greenhouse.io/clearcover", "Insurance"),
    ("Kin Insurance", "https://boards.greenhouse.io/kininsurance", "Insurance"),
    ("Hippo Insurance", "https://boards.greenhouse.io/hippo", "Insurance"),
    ("Root Insurance", "https://boards.greenhouse.io/rootinsurance", "Insurance"),
    ("Policygenius", "https://boards.greenhouse.io/policygenius", "Insurance"),
    ("Lemonade", "https://boards.greenhouse.io/lemonade", "Insurance"),

    # 5. Solar, Energy & Utilities
    ("Redwood Materials", "https://boards.greenhouse.io/redwoodmaterials", "Solar, Energy & Utilities"),
    ("ChargePoint", "https://boards.greenhouse.io/chargepoint", "Solar, Energy & Utilities"),
    ("Arcadia Power", "https://boards.greenhouse.io/arcadia", "Solar, Energy & Utilities"),
    ("Aurora Solar", "https://boards.greenhouse.io/aurorasolar", "Solar, Energy & Utilities"),
    ("Form Energy", "https://boards.greenhouse.io/formenergy", "Solar, Energy & Utilities"),
    ("Nextracker", "https://boards.greenhouse.io/nextracker", "Solar, Energy & Utilities"),
    ("Stem", "https://boards.greenhouse.io/stem", "Solar, Energy & Utilities"),

    # 6. Aerospace & Defense
    ("Anduril Industries", "https://www.anduril.com/open-roles", "Aerospace & Defense"),
    ("Astranis", "https://boards.greenhouse.io/astranis", "Aerospace & Defense"),
    ("BlackSky Technology", "https://boards.greenhouse.io/blacksky", "Aerospace & Defense"),
    ("Applied Intuition Defense", "https://boards.greenhouse.io/appliedintuition", "Aerospace & Defense"),
    ("Rocket Lab", "https://boards.greenhouse.io/rocketlab", "Aerospace & Defense"),
    ("Relativity Space", "https://boards.greenhouse.io/relativity", "Aerospace & Defense"),
    ("Planet Labs", "https://boards.greenhouse.io/planetlabs", "Aerospace & Defense"),
    ("Epirus", "https://boards.greenhouse.io/epirus", "Aerospace & Defense"),
    ("Sierra Space", "https://boards.greenhouse.io/sierraspace", "Aerospace & Defense"),
    ("Shield AI", "https://boards.greenhouse.io/shieldai", "Aerospace & Defense"),

    # 7. Pharma & Biotechnology
    ("Twist Bioscience", "https://boards.greenhouse.io/twistbioscience", "Pharma & Biotechnology"),
    ("Beam Therapeutics", "https://boards.greenhouse.io/beamtherapeutics", "Pharma & Biotechnology"),
    ("Ginkgo Bioworks", "https://boards.greenhouse.io/ginkgobioworks", "Pharma & Biotechnology"),
    ("Recursion Pharmaceuticals", "https://boards.greenhouse.io/recursion", "Pharma & Biotechnology"),
    ("Tempus AI", "https://boards.greenhouse.io/tempus", "Pharma & Biotechnology"),
    ("Sana Biotechnology", "https://boards.greenhouse.io/sanabiotechnology", "Pharma & Biotechnology"),
]

verified_list = []
for name, url, ind in candidate_companies:
    try:
        r = requests.get(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.text) > 15000:
            verified_list.append((name, url, ind, len(r.text)))
            print(f"OK: {name} ({ind}) -> Length: {len(r.text)}")
        else:
            print(f"FAIL ({r.status_code}): {name}")
    except Exception as e:
        print(f"ERR: {name} -> {e}")

print(f"\nTotal Verified High-Yield Companies: {len(verified_list)}")

