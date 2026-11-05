import urllib.request
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

test_cases = [
    ("Prime Medicine", "6184175004", "primemedicine", "https://primemedicine.com/careers/"),
    ("Affirm", "8016833003", "affirm", "https://www.affirm.com/careers"),
    ("Astranis", "4613477006", "astranis", "https://www.astranis.com/careers"),
    ("Vercel", "5798406004", "vercel", "https://vercel.com/careers"),
    ("Reddit", "8211850", "reddit", "https://boards.greenhouse.io/reddit"),
    ("Box", "8133235", "boxinc", "https://www.box.com/careers"),
    ("Rocket Lab", "7997781003", "rocketlab", "https://boards.greenhouse.io/rocketlab"),
    ("Carta", "7998678003", "carta", "https://carta.com/careers/"),
    ("Scale AI", "4720422005", "scaleai", "https://scale.com/careers"),
    ("Twilio", "8350197", "twilio", "https://www.twilio.com/en-us/company/jobs"),
]

for name, jid, slug, c_url in test_cases:
    print(f"\n--- {name} (Job ID: {jid}) ---")

    # Option A: boards.greenhouse.io/{slug}/jobs/{jid}
    url_a = f"https://boards.greenhouse.io/{slug}/jobs/{jid}"
    try:
        req = urllib.request.Request(url_a, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"  Option A (boards.greenhouse.io): {resp.status} (Length: {len(resp.read())})")
    except Exception as e:
        print(f"  Option A (boards.greenhouse.io) FAILED: {e}")

    # Option B: {company_url}?gh_jid={jid}
    base = c_url.rstrip("/")
    url_b = f"{base}/?gh_jid={jid}"
    try:
        req = urllib.request.Request(url_b, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"  Option B ({url_b}): {resp.status} (Length: {len(resp.read())})")
    except Exception as e:
        print(f"  Option B ({url_b}) FAILED: {e}")

