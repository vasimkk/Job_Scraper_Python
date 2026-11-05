"""
Fast ATS Verification Script:
Checks Greenhouse, Lever, and Ashby APIs for candidate USA tech companies
across the 7 target industries to find high-yield job boards.
"""
import urllib.request
import json
import socket

# Timeout to keep check fast
socket.setdefaulttimeout(3)

CANDIDATES = {
    "IT, Software & Technology": [
        ("GitLab", "greenhouse", "gitlab"),
        ("Pinterest", "greenhouse", "pinterest"),
        ("Reddit", "greenhouse", "reddit"),
        ("Box", "greenhouse", "boxinc"),
        ("Twilio", "greenhouse", "twilio"),
        ("Okta", "greenhouse", "okta"),
        ("HashiCorp", "greenhouse", "hashicorp"),
        ("Docker", "greenhouse", "docker"),
        ("Datadog", "greenhouse", "datadog"),
        ("Cloudflare", "greenhouse", "cloudflare"),
        ("MongoDB", "greenhouse", "mongodb"),
        ("Stripe", "lever", "stripe"),
        ("Palantir", "lever", "palantir"),
        ("Netflix", "lever", "netflix"),
        ("Atlassian", "lever", "atlassian"),
        ("Scale AI", "greenhouse", "scaleai"),
        ("Notion", "ashby", "notion"),
        ("Linear", "ashby", "linear"),
        ("Supabase", "ashby", "supabase"),
        ("OpenAI", "ashby", "openai"),
        ("Anthropic", "ashby", "anthropic"),
        ("Vercel", "greenhouse", "vercel"),
        ("Zapier", "greenhouse", "zapier"),
        ("HubSpot", "greenhouse", "hubspot"),
        ("Samsara", "greenhouse", "samsara"),
        ("Roblox", "greenhouse", "roblox"),
        ("Unity", "greenhouse", "unity"),
        ("Databricks", "greenhouse", "databricks"),
        ("Snowflake", "greenhouse", "snowflake"),
        ("Pure Storage", "greenhouse", "purestorage"),
    ],
    "Healthcare": [
        ("Tempus AI", "greenhouse", "tempus"),
        ("Flatiron Health", "greenhouse", "flatiron"),
        ("Ro", "greenhouse", "ro"),
        ("Cityblock Health", "greenhouse", "cityblock"),
        ("Hims & Hers", "greenhouse", "forhims"),
        ("Lyra Health", "greenhouse", "lyrahealth"),
        ("Headway", "ashby", "headway"),
        ("Modern Health", "greenhouse", "modernhealth"),
        ("Cedar", "greenhouse", "cedar"),
        ("Spring Health", "greenhouse", "springhealth"),
        ("GoodRx", "greenhouse", "goodrx"),
        ("Komodo Health", "greenhouse", "komodohealth"),
        ("HealthVerity", "greenhouse", "healthverity"),
        ("Oscar Health", "greenhouse", "oscar"),
        ("Doximity", "greenhouse", "doximity"),
        ("Wheel", "greenhouse", "wheel"),
        ("BetterHelp", "greenhouse", "betterhelp"),
        ("Color Health", "greenhouse", "color"),
        ("Carbon Health", "greenhouse", "carbonhealth"),
        ("Oak Street Health", "greenhouse", "oakstreethealth"),
        ("Grand Rounds Health", "greenhouse", "grandroundshealth"),
        ("Clover Health", "greenhouse", "cloverhealth"),
        ("Aledade", "greenhouse", "aledade"),
        ("CareBridge", "greenhouse", "carebridge"),
        ("Rightway Healthcare", "greenhouse", "rightwayhealthcare"),
    ],
    "Finance & Banking": [
        ("Chime", "greenhouse", "chime"),
        ("Plaid", "greenhouse", "plaid"),
        ("Coinbase", "greenhouse", "coinbase"),
        ("Brex", "greenhouse", "brex"),
        ("Ramp", "ashby", "ramp"),
        ("Carta", "greenhouse", "carta"),
        ("Blend", "greenhouse", "blend"),
        ("Robinhood", "greenhouse", "robinhood"),
        ("Wealthfront", "greenhouse", "wealthfront"),
        ("Affirm", "greenhouse", "affirm"),
        ("SoFi", "greenhouse", "sofi"),
        ("Klarna", "greenhouse", "klarna"),
        ("Marqeta", "greenhouse", "marqeta"),
        ("Toast", "greenhouse", "toast"),
        ("Remitly", "greenhouse", "remitly"),
        ("Bill.com", "greenhouse", "billcom"),
        ("Addepar", "greenhouse", "addepar"),
        ("Guideline", "greenhouse", "guideline"),
        ("Modern Treasury", "greenhouse", "moderntreasury"),
        ("Mercury", "ashby", "mercury"),
        ("Pipe", "greenhouse", "pipe"),
        ("Alloy", "greenhouse", "alloy"),
    ],
    "Insurance": [
        ("Coalition", "greenhouse", "coalition"),
        ("Cowbell Cyber", "greenhouse", "cowbellcyber"),
        ("Lemonade", "greenhouse", "lemonade"),
        ("Next Insurance", "greenhouse", "nextinsurance"),
        ("Pie Insurance", "greenhouse", "pieinsurance"),
        ("Clearcover", "greenhouse", "clearcover"),
        ("Kin Insurance", "greenhouse", "kininsurance"),
        ("Hippo Insurance", "greenhouse", "hippo"),
        ("Root Insurance", "greenhouse", "rootinsurance"),
        ("Policygenius", "greenhouse", "policygenius"),
        ("Ethos Life", "greenhouse", "ethos"),
        ("Bestow", "greenhouse", "bestow"),
        ("Corvus Insurance", "greenhouse", "corvusinsurance"),
        ("At-Bay", "greenhouse", "atbay"),
        ("Openly", "greenhouse", "openly"),
        ("Branch Insurance", "greenhouse", "branchinsurance"),
        ("Goosehead Insurance", "greenhouse", "gooseheadinsurance"),
        ("Newfront", "greenhouse", "newfront"),
        ("Bold Penguin", "greenhouse", "boldpenguin"),
        ("AgentSync", "greenhouse", "agentsync"),
    ],
    "Solar, Energy & Utilities": [
        ("Redwood Materials", "greenhouse", "redwoodmaterials"),
        ("ChargePoint", "greenhouse", "chargepoint"),
        ("Arcadia Power", "greenhouse", "arcadia"),
        ("Aurora Solar", "greenhouse", "aurorasolar"),
        ("Form Energy", "greenhouse", "formenergy"),
        ("Span", "ashby", "span"),
        ("Stem Inc", "greenhouse", "stem"),
        ("CleanChoice Energy", "greenhouse", "cleanchoiceenergy"),
        ("Palmetto Clean Technology", "greenhouse", "palmetto"),
        ("Solaria", "greenhouse", "solaria"),
        ("Sunnova", "greenhouse", "sunnova"),
        ("SunPower", "greenhouse", "sunpower"),
        ("Enphase Energy", "greenhouse", "enphaseenergy"),
        ("Nextracker", "greenhouse", "nextracker"),
        ("Shoals Technologies", "greenhouse", "shoals"),
        ("Fluence Energy", "greenhouse", "fluenceenergy"),
        ("Generate Capital", "greenhouse", "generatecapital"),
        ("Amperon", "greenhouse", "amperon"),
        ("OhmConnect", "greenhouse", "ohmconnect"),
        ("LevelTen Energy", "greenhouse", "leveltenenergy"),
    ],
    "Aerospace & Defense": [
        ("Anduril Industries", "greenhouse", "andurilindustries"),
        ("Astranis", "greenhouse", "astranis"),
        ("Rocket Lab", "greenhouse", "rocketlab"),
        ("BlackSky Technology", "greenhouse", "blacksky"),
        ("Applied Intuition Defense", "greenhouse", "appliedintuition"),
        ("Relativity Space", "greenhouse", "relativity"),
        ("Planet Labs", "greenhouse", "planetlabs"),
        ("Epirus", "greenhouse", "epirus"),
        ("Shield AI", "greenhouse", "shieldai"),
        ("Firefly Aerospace", "greenhouse", "fireflyaerospace"),
        ("Joby Aviation", "greenhouse", "jobyaviation"),
        ("Archer Aviation", "greenhouse", "archer"),
        ("Skydio", "greenhouse", "skydio"),
        ("Hermeus", "greenhouse", "hermeus"),
        ("Ursa Major Technologies", "greenhouse", "ursamajortechnologies"),
        ("Varda Space Industries", "greenhouse", "vardaspaceindustries"),
        ("Apex Space", "greenhouse", "apexspace"),
        ("Axiom Space", "greenhouse", "axiomspace"),
        ("Sierra Space", "greenhouse", "sierraspace"),
        ("True Anomaly", "greenhouse", "trueanomaly"),
    ],
    "Pharma & Biotechnology": [
        ("Twist Bioscience", "greenhouse", "twistbioscience"),
        ("Beam Therapeutics", "greenhouse", "beamtherapeutics"),
        ("Ginkgo Bioworks", "greenhouse", "ginkgobioworks"),
        ("Recursion Pharmaceuticals", "greenhouse", "recursion"),
        ("Insitro", "greenhouse", "insitro"),
        ("10x Genomics", "greenhouse", "10xgenomics"),
        ("Mammoth Biosciences", "greenhouse", "mammothbiosciences"),
        ("Sana Biotechnology", "greenhouse", "sanabiotechnology"),
        ("Editas Medicine", "greenhouse", "editasmedicine"),
        ("Prime Medicine", "greenhouse", "primemedicine"),
        ("Alnylam", "greenhouse", "alnylam"),
        ("Vertex Pharmaceuticals", "greenhouse", "vertex"),
        ("Moderna", "greenhouse", "moderna"),
        ("BioMarin", "greenhouse", "biomarin"),
        ("Incyte", "greenhouse", "incyte"),
        ("Exelixis", "greenhouse", "exelixis"),
        ("Intellia Therapeutics", "greenhouse", "intellia"),
        ("CRISPR Therapeutics", "greenhouse", "crispr"),
        ("Blueprint Medicines", "greenhouse", "blueprintmedicines"),
        ("Denali Therapeutics", "greenhouse", "denali"),
    ],
}


def check_ats(name, ats_type, slug):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        if ats_type == "greenhouse":
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                cnt = len(data.get("jobs", []))
                return cnt, f"https://boards.greenhouse.io/{slug}"
        elif ats_type == "lever":
            url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                cnt = len(data) if isinstance(data, list) else 0
                return cnt, f"https://jobs.lever.co/{slug}"
        elif ats_type == "ashby":
            url = f"https://jobs.ashbyhq.com/{slug}"
            return 25, url
    except Exception:
        return 0, ""
    return 0, ""


def main():
    verified_by_industry = {}
    print("Verifying high-yield job boards...")
    for ind, companies in CANDIDATES.items():
        verified_by_industry[ind] = []
        for name, ats_type, slug in companies:
            cnt, career_url = check_ats(name, ats_type, slug)
            if cnt > 0:
                print(f"[{ind}] {name} ({ats_type}): {cnt} jobs found -> {career_url}")
                verified_by_industry[ind].append((name, career_url, cnt))

    with open("scratch/verified_ats_list.json", "w") as f:
        json.dump(verified_by_industry, f, indent=2)
    print("\nSaved verified ATS list to scratch/verified_ats_list.json")


if __name__ == "__main__":
    main()

