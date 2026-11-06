import sys
sys.path.insert(0, ".")
from scraper_agent.classifiers.location_parser import US_STATE_NAMES_TO_CODE

paths = [
    "/job/Colorado-Denver-Surrounding-Virtual-Address/Senior-Implementation-Engineer-Remote_R576987",
    "/job/Florida-Weston-3365-Enterprise-Avenue/Robotics-Systems-Engineer_R576762",
    "/job/Portage-Michigan/Senior-Test-Engineer_R569419-1",
    "/job/Phoenix-Arizona/Senior-Implementation-Engineer_R576912",
    "/job/Vancouver-Canada/Senior-Implementation-Engineer_R577006",
    "/job/Sunshine-Coast-Australia/Associate-Field-Service_R563489",
]

for p in paths:
    loc_part = p.strip("/").split("/")[1]
    tokens = [t.lower() for t in loc_part.split("-")]
    found_st = None
    for t in tokens:
        if t in US_STATE_NAMES_TO_CODE:
            found_st = US_STATE_NAMES_TO_CODE[t]
            break
    print(f"{p} -> found US state: {found_st}")
