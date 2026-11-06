import urllib.request
import json

url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/job/US-CA-Santa-Clara/Senior-Site-Reliability-Engineer---HPC_JR2013271"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print("SUCCESS! Keys:", data.keys())
        info = data.get("jobPostingInfo", {})
        print("Title:", info.get("title"))
        print("Location:", info.get("location"))
        print("TimeType:", info.get("timeType"))
        print("Description length:", len(info.get("jobDescription", "")))
except Exception as e:
    print(f"Error: {e}")

