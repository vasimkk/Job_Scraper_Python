import urllib.request
import json

api_url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"
payload = json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}).encode("utf-8")
req = urllib.request.Request(
    api_url,
    data=payload,
    headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    },
    method="POST",
)
with urllib.request.urlopen(req, timeout=12) as resp:
    data = json.loads(resp.read().decode())
    print("Page 1:")
    print("  total:", data.get("total"))
    print("  jobPostings count:", len(data.get("jobPostings", [])))
    if data.get("jobPostings"):
        print("  sample title:", data["jobPostings"][0].get("title"))

# Try Page 2 with offset 20
payload2 = json.dumps({"appliedFacets": {}, "limit": 20, "offset": 20, "searchText": ""}).encode("utf-8")
req2 = urllib.request.Request(
    api_url,
    data=payload2,
    headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    },
    method="POST",
)
with urllib.request.urlopen(req2, timeout=12) as resp:
    data2 = json.loads(resp.read().decode())
    print("Page 2:")
    print("  jobPostings count:", len(data2.get("jobPostings", [])))
    if data2.get("jobPostings"):
        print("  sample title:", data2["jobPostings"][0].get("title"))
