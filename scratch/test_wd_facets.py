import urllib.request
import json

url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"
payload = json.dumps({"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}).encode("utf-8")
req = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode())
    print("Keys in response:", data.keys())
    facets = data.get("facets", [])
    print(f"Number of facets: {len(facets)}")
    for f in facets:
        print("Facet:", f.get("facetParameter"), f.get("descriptor"))
        if f.get("facetParameter") in ("locationCountry", "country", "locations"):
            print("Values sample:", f.get("values", [])[:5])

