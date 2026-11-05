import sys
sys.path.insert(0, ".")
import psycopg

conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
cur = conn.cursor()

# Map of company name -> verified ATS board URL and industry
COMPANY_ATS_MAP = {
    # 1. IT, Software & Technology
    "Figma": ("https://boards.greenhouse.io/figma", "IT, Software & Technology"),
    "Datadog": ("https://boards.greenhouse.io/datadog", "IT, Software & Technology"),
    "Supabase": ("https://boards.greenhouse.io/supabase", "IT, Software & Technology"),
    "Notion": ("https://boards.greenhouse.io/notion", "IT, Software & Technology"),
    "Linear": ("https://jobs.ashbyhq.com/linear", "IT, Software & Technology"),
    "Vercel": ("https://boards.greenhouse.io/vercel", "IT, Software & Technology"),
    "Elastic": ("https://boards.greenhouse.io/elastic", "IT, Software & Technology"),
    "Cockroach Labs": ("https://boards.greenhouse.io/cockroachlabs", "IT, Software & Technology"),
    "Airtable": ("https://boards.greenhouse.io/airtable", "IT, Software & Technology"),
    "Postman": ("https://boards.greenhouse.io/postman", "IT, Software & Technology"),
    "Gusto": ("https://boards.greenhouse.io/gusto", "IT, Software & Technology"),
    "Rippling": ("https://boards.greenhouse.io/rippling", "IT, Software & Technology"),
    "Retool": ("https://jobs.ashbyhq.com/retool", "IT, Software & Technology"),
    "Webflow": ("https://boards.greenhouse.io/webflow", "IT, Software & Technology"),
    "Braze": ("https://boards.greenhouse.io/braze", "IT, Software & Technology"),
    "Klaviyo": ("https://boards.greenhouse.io/klaviyo", "IT, Software & Technology"),
    "Zapier": ("https://jobs.lever.co/zapier", "IT, Software & Technology"),
    "Amplitude": ("https://boards.greenhouse.io/amplitude", "IT, Software & Technology"),
    "Docker": ("https://jobs.lever.co/docker", "IT, Software & Technology"),
    "Databricks": ("https://boards.greenhouse.io/databricks", "IT, Software & Technology"),
    "Confluent": ("https://boards.greenhouse.io/confluent", "IT, Software & Technology"),

    # 2. Healthcare
    "Oscar Health": ("https://boards.greenhouse.io/oscar", "Healthcare"),
    "Komodo Health": ("https://boards.greenhouse.io/komodohealth", "Healthcare"),
    "Doximity": ("https://boards.greenhouse.io/doximity", "Healthcare"),
    "BetterHelp": ("https://boards.greenhouse.io/betterhelp", "Healthcare"),
    "Wheel": ("https://boards.greenhouse.io/wheel", "Healthcare"),
    "Ro": ("https://boards.greenhouse.io/ro", "Healthcare"),
    "GoodRx": ("https://boards.greenhouse.io/goodrx", "Healthcare"),
    "Datavant": ("https://boards.greenhouse.io/datavant", "Healthcare"),
    "Flatiron Health": ("https://boards.greenhouse.io/flatiron", "Healthcare"),
    "Maven Clinic": ("https://jobs.lever.co/mavenclinic", "Healthcare"),
    "Cedar": ("https://boards.greenhouse.io/cedar", "Healthcare"),
    "Cityblock Health": ("https://boards.greenhouse.io/cityblockhealth", "Healthcare"),
    "HealthVerity": ("https://boards.greenhouse.io/healthverity", "Healthcare"),

    # 3. Finance & Banking
    "Stripe": ("https://boards.greenhouse.io/stripe", "Finance & Banking"),
    "Plaid": ("https://boards.greenhouse.io/plaid", "Finance & Banking"),
    "Ramp": ("https://jobs.ashbyhq.com/ramp", "Finance & Banking"),
    "Brex": ("https://boards.greenhouse.io/brex", "Finance & Banking"),
    "Chime": ("https://boards.greenhouse.io/chime", "Finance & Banking"),
    "Coinbase": ("https://boards.greenhouse.io/coinbase", "Finance & Banking"),
    "Robinhood": ("https://boards.greenhouse.io/robinhood", "Finance & Banking"),
    "Wealthfront": ("https://boards.greenhouse.io/wealthfront", "Finance & Banking"),
    "Affirm": ("https://boards.greenhouse.io/affirm", "Finance & Banking"),
    "Carta": ("https://boards.greenhouse.io/carta", "Finance & Banking"),
    "Marqeta": ("https://boards.greenhouse.io/marqeta", "Finance & Banking"),

    # 4. Insurance
    "Lemonade": ("https://boards.greenhouse.io/lemonade", "Insurance"),
    "Hippo Insurance": ("https://boards.greenhouse.io/hippo", "Insurance"),
    "Next Insurance": ("https://boards.greenhouse.io/nextinsurance", "Insurance"),
    "Policygenius": ("https://boards.greenhouse.io/policygenius", "Insurance"),
    "Root Insurance": ("https://boards.greenhouse.io/rootinsurance", "Insurance"),
    "Kin Insurance": ("https://boards.greenhouse.io/kininsurance", "Insurance"),
    "Coalition": ("https://boards.greenhouse.io/coalition", "Insurance"),
    "Ethos": ("https://jobs.lever.co/ethos", "Insurance"),
    "Corvus Insurance": ("https://boards.greenhouse.io/corvusinsurance", "Insurance"),
    "Clearcover": ("https://boards.greenhouse.io/clearcover", "Insurance"),

    # 5. Solar, Energy & Utilities
    "Form Energy": ("https://boards.greenhouse.io/formenergy", "Solar, Energy & Utilities"),
    "Enphase Energy": ("https://boards.greenhouse.io/enphase", "Solar, Energy & Utilities"),
    "Palmetto": ("https://boards.greenhouse.io/palmetto", "Solar, Energy & Utilities"),
    "Rivian": ("https://boards.greenhouse.io/rivian", "Solar, Energy & Utilities"),
    "Arcadia Power": ("https://boards.greenhouse.io/arcadia", "Solar, Energy & Utilities"),
    "Redwood Materials": ("https://boards.greenhouse.io/redwoodmaterials", "Solar, Energy & Utilities"),
    "Commonwealth Fusion Systems": ("https://boards.greenhouse.io/cfs", "Solar, Energy & Utilities"),
    "ChargePoint": ("https://boards.greenhouse.io/chargepoint", "Solar, Energy & Utilities"),
    "Aurora Solar": ("https://boards.greenhouse.io/aurorasolar", "Solar, Energy & Utilities"),

    # 6. Aerospace & Defense
    "Anduril Industries": ("https://www.anduril.com/open-roles", "Aerospace & Defense"),
    "Astranis": ("https://boards.greenhouse.io/astranis", "Aerospace & Defense"),
    "BlackSky Technology": ("https://boards.greenhouse.io/blacksky", "Aerospace & Defense"),
    "Applied Intuition Defense": ("https://boards.greenhouse.io/appliedintuition", "Aerospace & Defense"),
    "Rocket Lab": ("https://boards.greenhouse.io/rocketlab", "Aerospace & Defense"),
    "Relativity Space": ("https://boards.greenhouse.io/relativity", "Aerospace & Defense"),
    "Planet Labs": ("https://boards.greenhouse.io/planetlabs", "Aerospace & Defense"),
    "Sierra Space": ("https://boards.greenhouse.io/sierraspace", "Aerospace & Defense"),
    "Shield AI": ("https://boards.greenhouse.io/shieldai", "Aerospace & Defense"),
    "Hermeus": ("https://boards.greenhouse.io/hermeus", "Aerospace & Defense"),
    "Stoke Space": ("https://boards.greenhouse.io/stokespace", "Aerospace & Defense"),
    "Firefly Aerospace": ("https://boards.greenhouse.io/fireflyaerospace", "Aerospace & Defense"),

    # 7. Pharma & Biotechnology
    "Recursion Pharmaceuticals": ("https://boards.greenhouse.io/recursion", "Pharma & Biotechnology"),
    "Ginkgo Bioworks": ("https://jobs.lever.co/ginkgobioworks", "Pharma & Biotechnology"),
    "Tempus AI": ("https://boards.greenhouse.io/tempus", "Pharma & Biotechnology"),
    "Beam Therapeutics": ("https://boards.greenhouse.io/beamtherapeutics", "Pharma & Biotechnology"),
    "Insitro": ("https://jobs.lever.co/insitro", "Pharma & Biotechnology"),
    "Twist Bioscience": ("https://boards.greenhouse.io/twistbioscience", "Pharma & Biotechnology"),
    "Moderna": ("https://boards.greenhouse.io/moderna", "Pharma & Biotechnology"),
    "Alnylam Pharmaceuticals": ("https://boards.greenhouse.io/alnylam", "Pharma & Biotechnology"),
}

# Update or insert into companies and job_sources
updated_sources = 0
for name, (url, ind) in COMPANY_ATS_MAP.items():
    # Update company
    cur.execute(
        """
        INSERT INTO companies (name, domain, career_url, industry, active)
        VALUES (%s, %s, %s, %s, TRUE)
        ON CONFLICT (name) DO UPDATE SET 
            career_url = EXCLUDED.career_url,
            industry = EXCLUDED.industry,
            active = TRUE
        RETURNING id;
        """,
        (name, f"{name.lower().replace(' ', '')}.com", url, ind)
    )
    cid = cur.fetchone()[0]

    # Update or insert job source
    cur.execute(
        "UPDATE job_sources SET source_url = %s, active = TRUE WHERE company_id = %s;",
        (url, cid)
    )
    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO job_sources (company_id, source_url, scraper_type, active) VALUES (%s, %s, 'playwright', TRUE);",
            (cid, url)
        )
    updated_sources += 1

conn.commit()
print(f"Updated {updated_sources} company ATS career URLs.")
conn.close()
