import sys
sys.path.insert(0, ".")
import time
from concurrent.futures import ThreadPoolExecutor
from scraper_agent.scrapers.base import BaseScraper

urls = [
    "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/US-CA-Santa-Clara/Senior-Site-Reliability-Engineer_JR1985473",
    "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/US-CA-Santa-Clara/Manager--Personnel-Security-Clearance_JR2023530",
    "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/US-OR-Hillsboro/Hardware-Validation-Engineer--Post-Silicon--PCIe-and-High-Speed-IO_JR2025171",
] * 5  # 15 jobs

t0 = time.time()
with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(BaseScraper.fetch_job_deep_info, urls))
dt = time.time() - t0

print(f"Fetched {len(results)} Workday deep jobs in {dt:.2f}s ({dt/len(results):.2f}s per job)!")
for r in results[:2]:
    print("Title:", r.get("title"))
    print("Loc:", r.get("location"))
    print("Desc length:", len(r.get("description") or ""))
