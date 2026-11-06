import urllib.request
import json

base = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite"
variants = [
    "/job/US-CA-Santa-Clara/Senior-Site-Reliability-Engineer_JR1985473",
    "/job/Senior-Site-Reliability-Engineer_JR1985473",
    "/jobs/JR1985473",
    "/job/JR1985473",
    "/job/Senior-Site-Reliability-Engineer",
]

for v in variants:
    url = f"{base}{v}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"SUCCESS {resp.status} for {url}")
            data = json.loads(resp.read().decode())
            print("Keys:", data.keys())
            break
    except Exception as e:
        print(f"FAILED {e} for {v}")

