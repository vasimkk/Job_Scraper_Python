import re

sample_paths = [
    "/job/US-CA-Santa-Clara/Senior-Site-Reliability-Engineer_JR1985473",
    "/job/US-CA-Remote/Senior-Product-Manager--AI-Physics_JR2021069",
    "/job/US-OR-Hillsboro/Hardware-Validation-Engineer_JR2025171",
    "/job/China-Shanghai/CPU-Performance-Developer-Technology-Engineer_JR2023977",
    "/job/Finland-Helsinki/Senior-Manager--Graphics-Systems-Software_JR2028247",
    "/job/Israel-Yokneam/Director--Software-Technology_JR2013271",
    "/job/Pittsburgh-PA/Medicare-Field-Sales--Allegheny_R-436457",
    "/job/United-Kingdom---London/Principal-AI-Architect_JR362633",
    "/job/Australia---Sydney/Public-Sector-Account-Executive_JR364993",
    "/job/Washington-DC/Director-Cybersecurity_R173038"
]

def parse_ext_path_loc(ext_path: str) -> str:
    # 1. /job/US-CA-Santa-Clara/ or /job/US-OR-Hillsboro/
    m1 = re.search(r"/job/US-([A-Z]{2})-([^/]+)/", ext_path)
    if m1:
        st, city = m1.group(1), m1.group(2).replace("-", " ")
        return f"{city}, {st}, United States"
    # 2. /job/City-ST/ e.g. /job/Pittsburgh-PA/ or /job/Washington-DC/
    m2 = re.search(r"/job/([A-Za-z]+)-([A-Z]{2})/", ext_path)
    if m2:
        city, st = m2.group(1), m2.group(2)
        return f"{city}, {st}, United States"
    # 3. /job/Country---City/ e.g. /job/United-Kingdom---London/
    m3 = re.search(r"/job/([A-Za-z-]+)---([A-Za-z-]+)/", ext_path)
    if m3:
        country, city = m3.group(1).replace("-", " "), m3.group(2).replace("-", " ")
        return f"{city}, {country}"
    # 4. /job/Country-City/ e.g. /job/China-Shanghai/
    m4 = re.search(r"/job/([A-Za-z]+)-([A-Za-z]+)/", ext_path)
    if m4:
        country, city = m4.group(1), m4.group(2)
        return f"{city}, {country}"
    return ""

for p in sample_paths:
    loc = parse_ext_path_loc(p)
    print(f"{p} -> '{loc}'")

