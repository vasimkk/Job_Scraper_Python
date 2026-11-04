import re
from typing import Tuple, List

# Core technology roles & skills keywords
TECH_KEYWORDS = [
    # Engineering & Development
    r"\bsoftware\b",
    r"\bdeveloper\b",
    r"\bengineer\b",
    r"\bengineering\b",
    r"\bfrontend\b",
    r"\bfront-end\b",
    r"\bbackend\b",
    r"\bback-end\b",
    r"\bfullstack\b",
    r"\bfull-stack\b",
    r"\bweb\b",
    r"\bmobile\b",
    r"\bios\b",
    r"\bandroid\b",
    r"\bfirmware\b",
    r"\bembedded\b",
    r"\bsystems?\b",
    r"\bkernel\b",
    # Data & AI/ML
    r"\bdata\b",
    r"\bmachine learning\b",
    r"\bml\b",
    r"\bai\b",
    r"\bartificial intelligence\b",
    r"\bdeep learning\b",
    r"\bnlp\b",
    r"\bcomputer vision\b",
    r"\bdata science\b",
    r"\bdata scientist\b",
    r"\bdata engineer\b",
    r"\bdata analyst\b",
    r"\banalytics\b",
    r"\bdatabase\b",
    r"\bdba\b",
    r"\bbig data\b",
    # Infrastructure, Cloud & DevOps
    r"\bdevops\b",
    r"\bsre\b",
    r"\bsite reliability\b",
    r"\bcloud\b",
    r"\binfrastructure\b",
    r"\bplatform\b",
    r"\bkubernetes\b",
    r"\bdocker\b",
    r"\baws\b",
    r"\bazure\b",
    r"\bgcp\b",
    r"\bterraform\b",
    r"\blinux\b",
    r"\bnetworking\b",
    # Quality Assurance & Testing
    r"\bqa\b",
    r"\bquality assurance\b",
    r"\btest\b",
    r"\bsdet\b",
    r"\bautomation\b",
    # Security
    r"\bsecurity\b",
    r"\bcybersecurity\b",
    r"\binfosec\b",
    r"\bpenetration\b",
    r"\bvulnerability\b",
    r"\bappsec\b",
    # Architecture & Product Tech
    r"\barchitect\b",
    r"\btechnical\b",
    r"\btech lead\b",
    r"\bcto\b",
    r"\bvpe\b",
    r"\bvp of engineering\b",
    r"\btechnical program manager\b",
    r"\btpm\b",
    # Programming Languages & Frameworks (often in titles)
    r"\bpython\b",
    r"\bjava\b",
    r"\bgolang\b",
    r"\bgo\b",
    r"\brust\b",
    r"\bc\+\+\b",
    r"\bc#\b",
    r"\bjavascript\b",
    r"\btypescript\b",
    r"\breact\b",
    r"\bnode\b",
    r"\bangular\b",
    r"\bvue\b",
]

# Explicit non-tech roles to avoid false positives when words like 'developer' or 'engineer' are used in other contexts (e.g. "Civil Engineer", "Business Development")
NON_TECH_PATTERNS = [
    r"\bcivil engineer\b",
    r"\bmechanical technician\b",
    r"\bbusiness development\b",
    r"\bsales representative\b",
    r"\baccount executive\b",
    r"\breceptionist\b",
    r"\bnurse\b",
    r"\bphysician\b",
    r"\bclinical specialist\b",
    r"\blegal counsel\b",
    r"\bparalegal\b",
    r"\bpayroll specialist\b",
    r"\btalent acquisition\b",
    r"\brecruiter\b",
    r"\boffice manager\b",
]

COMPILED_TECH_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in TECH_KEYWORDS]
COMPILED_NON_TECH_REGEX = [
    re.compile(pattern, re.IGNORECASE) for pattern in NON_TECH_PATTERNS
]


def is_technology_job(title: str, description: str = "") -> Tuple[bool, List[str]]:
    """
    Evaluates whether a job posting belongs to the technology/software/data domain.
    Returns:
        (is_tech: bool, matched_keywords: List[str])
    """
    title_clean = title.strip()
    matched_keywords = []

    # First check non-tech patterns in title
    for rx in COMPILED_NON_TECH_REGEX:
        if rx.search(title_clean):
            # If explicit non-tech title pattern matched, verify if it also has explicit software/tech overrides
            if not any(
                k in title_clean.lower()
                for k in ["software", "tech", "data", "engineer", "developer", "cloud"]
            ):
                return False, []

    # Match in title (highest confidence)
    for rx in COMPILED_TECH_REGEX:
        match = rx.search(title_clean)
        if match:
            matched_keywords.append(match.group(0).lower())

    if matched_keywords:
        return True, list(set(matched_keywords))

    # If title wasn't decisive, examine the first 500 characters of description
    desc_snippet = description[:500]
    for rx in COMPILED_TECH_REGEX:
        match = rx.search(desc_snippet)
        if match:
            matched_keywords.append(match.group(0).lower())

    # Require at least 2 distinct tech keywords from description if none in title
    unique_matches = list(set(matched_keywords))
    if len(unique_matches) >= 2:
        return True, unique_matches

    return False, []

