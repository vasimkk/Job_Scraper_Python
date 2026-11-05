import requests

more_boards = [
    # Insurance
    ("Coalition", "https://boards.greenhouse.io/coalition", "Insurance"),
    ("Lemonade Inc", "https://boards.greenhouse.io/lemonadeinc", "Insurance"),
    ("Kin Insurance", "https://boards.greenhouse.io/kin", "Insurance"),
    ("Root", "https://boards.greenhouse.io/root", "Insurance"),
    ("Clearcover", "https://boards.greenhouse.io/clearcover", "Insurance"),
    ("Corvus", "https://boards.greenhouse.io/corvus", "Insurance"),
    ("Cowbell Cyber", "https://boards.greenhouse.io/cowbellcyber", "Insurance"),
    ("Pie Insurance", "https://boards.greenhouse.io/pieinsurance", "Insurance"),

    # Healthcare
    ("Oscar Health", "https://boards.greenhouse.io/oscar", "Healthcare"),
    ("Komodo Health", "https://boards.greenhouse.io/komodohealth", "Healthcare"),
    ("HealthVerity", "https://boards.greenhouse.io/healthverity", "Healthcare"),
    ("Doximity", "https://boards.greenhouse.io/doximity", "Healthcare"),
    ("Wheel", "https://boards.greenhouse.io/wheel", "Healthcare"),
    ("Lyra Health", "https://boards.greenhouse.io/lyrahealth", "Healthcare"),
    ("Hims & Hers", "https://boards.greenhouse.io/forhims", "Healthcare"),
    ("Ro", "https://boards.greenhouse.io/roco", "Healthcare"),
    ("Headway", "https://jobs.ashbyhq.com/headway", "Healthcare"),

    # Solar & Energy
    ("Stem", "https://boards.greenhouse.io/stem", "Solar, Energy & Utilities"),
    ("Nextracker", "https://boards.greenhouse.io/nextracker", "Solar, Energy & Utilities"),
    ("Solaria", "https://boards.greenhouse.io/solaria", "Solar, Energy & Utilities"),
    ("SunPower", "https://boards.greenhouse.io/sunpower", "Solar, Energy & Utilities"),
    ("Ampt", "https://boards.greenhouse.io/ampt", "Solar, Energy & Utilities"),
    ("Form Energy", "https://boards.greenhouse.io/formenergyinc", "Solar, Energy & Utilities"),

    # Aerospace & Defense
    ("Relativity Space", "https://boards.greenhouse.io/relativity", "Aerospace & Defense"),
    ("Planet Labs", "https://boards.greenhouse.io/planetlabs", "Aerospace & Defense"),
    ("Ursa Major", "https://boards.greenhouse.io/ursamajortechnologies", "Aerospace & Defense"),
    ("Shield AI", "https://boards.greenhouse.io/shieldaiinc", "Aerospace & Defense"),
    ("Joby", "https://boards.greenhouse.io/joby", "Aerospace & Defense"),
    ("Epirus", "https://boards.greenhouse.io/epirus", "Aerospace & Defense"),

    # Pharma & Biotech
    ("Twist Bioscience", "https://boards.greenhouse.io/twistbioscience", "Pharma & Biotechnology"),
    ("Beam Therapeutics", "https://boards.greenhouse.io/beamtherapeutics", "Pharma & Biotechnology"),
    ("Sana Biotechnology", "https://boards.greenhouse.io/sanabiotechnology", "Pharma & Biotechnology"),
    ("Recursion", "https://boards.greenhouse.io/recursionpharma", "Pharma & Biotechnology"),
    ("Ginkgo", "https://boards.greenhouse.io/ginkgobioworks", "Pharma & Biotechnology"),
    ("Denali Therapeutics", "https://boards.greenhouse.io/denalitherapeutics", "Pharma & Biotechnology"),
    ("Blueprint Medicines", "https://boards.greenhouse.io/blueprintmedicines", "Pharma & Biotechnology"),

    # IT & Fintech
    ("Databricks", "https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    ("Fastly", "https://boards.greenhouse.io/fastly", "IT, Software & Technology"),
    ("Twilio", "https://boards.greenhouse.io/twilio", "IT, Software & Technology"),
    ("MongoDB", "https://boards.greenhouse.io/mongodb", "IT, Software & Technology"),
    ("Okta", "https://boards.greenhouse.io/okta", "IT, Software & Technology"),
    ("Gusto", "https://boards.greenhouse.io/gusto", "IT, Software & Technology"),
    ("Ramp", "https://jobs.ashbyhq.com/ramp", "Finance & Banking"),
    ("Carta", "https://boards.greenhouse.io/carta", "Finance & Banking"),
    ("Blend", "https://boards.greenhouse.io/blend", "Finance & Banking"),
    ("Brex", "https://boards.greenhouse.io/brex", "Finance & Banking"),
]

verified = []
for name, url, ind in more_boards:
    try:
        r = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.text) > 20000:
            print(f"VERIFIED: {name} ({ind}) -> {url} [Length: {len(r.text)}]")
            verified.append((name, url, ind))
    except Exception:
        pass

print(f"\nTotal Verified: {len(verified)}")

