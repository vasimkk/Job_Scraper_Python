import sys
sys.path.insert(0, ".")
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location, detect_international_country

jds = [
    {
        "title": "Senior AI Platform Engineer - 220862",
        "loc": "Remote",
        "desc": """Senior AI Platform Engineer - 220862
Full Time
Remote

Bengaluru, Karnataka, India | Hyderabad, Telangana, India

Posted 8 days ago
Apply

Our Company
At Teradata...
Employees in this position are also eligible to participate in the Company’s comprehensive benefits programs, which include healthcare... a 401(k)-retirement savings plan... United States...
"""
    },
    {
        "title": "Senior Director, Product Management - 220579",
        "loc": "Hybrid",
        "desc": """Senior Director, Product Management - 220579
Full Time
Hybrid

Bengaluru, Karnataka, India | Karnataka, India

Posted 8 days ago
Apply
"""
    },
    {
        "title": "Senior Manager, Software Engineering - 220860",
        "loc": "Hybrid",
        "desc": """Senior Manager, Software Engineering - 220860
Full Time
Hybrid

Bengaluru, Karnataka, India | Hyderabad, Telangana, India | Pune, Maharashtra, India
"""
    },
    {
        "title": "Senior Manager, Partner Development Executive – Global ISV Partnerships - 220410",
        "loc": "Remote",
        "desc": """Senior Manager, Partner Development Executive – Global ISV Partnerships - 220410
Full Time
Remote

United States

Posted 8 days ago
Apply
US Pay Rate: $212,700.00 - $319,000.00
"""
    },
    {
        "title": "Manager, Field Marketing - 220829",
        "loc": "Hybrid",
        "desc": """Manager, Field Marketing - 220829
Full Time
Hybrid

Miami, FL, USA

Posted 8 days ago
Apply
"""
    },
    {
        "title": "Staff Global Program Manager - 220757",
        "loc": "Remote",
        "desc": """Staff Global Program Manager - 220757
Full Time
Remote

India

Posted 9 days ago
Apply
"""
    },
    {
        "title": "Staff Program Manager, FinOps and Procurement Operations - 220802",
        "loc": "Hybrid",
        "desc": """Staff Program Manager, FinOps and Procurement Operations - 220802
Full Time
Hybrid

Madhapur, Hyderabad, Telangana, India | India

Posted 9 days ago
Apply
"""
    }
]

for idx, j in enumerate(jds, 1):
    c, s, co, r = parse_location(j["loc"], j["title"], j["desc"])
    is_us = is_usa_location(j["loc"], j["title"], j["desc"], city=c, state=s, country=co)
    print(f"Job {idx}: {j['title'][:40]} | RawLoc: '{j['loc']}' -> Parsed: (City={c}, State={s}, Country={co}) -> is_usa={is_us}")

