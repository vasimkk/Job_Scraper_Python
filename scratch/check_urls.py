import requests

urls = [
    "https://boards.greenhouse.io/fireflyaerospace",
    "https://boards.greenhouse.io/cfs",
    "https://boards.greenhouse.io/cedar",
    "https://boards.greenhouse.io/brex",
    "https://boards.greenhouse.io/beamtherapeutics",
    "https://boards.greenhouse.io/chime",
    "https://boards.greenhouse.io/coinbase",
    "https://boards.greenhouse.io/plaid",
    "https://boards.greenhouse.io/robinhood",
    "https://boards.greenhouse.io/databricks",
    "https://boards.greenhouse.io/gusto",
    "https://boards.greenhouse.io/rippling",
]

for u in urls:
    try:
        r = requests.get(u, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        print(f"{u} -> Status: {r.status_code}, Length: {len(r.text)}")
    except Exception as e:
        print(f"{u} -> Err: {e}")

