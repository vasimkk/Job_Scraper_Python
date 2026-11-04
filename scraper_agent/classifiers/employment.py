import re
from typing import Optional, Dict, Any

# Regex patterns for contract employment
CONTRACT_PATTERNS = [
    r"\bcontract\b",
    r"\bcontractor\b",
    r"\bc2c\b",
    r"\bcorp-to-corp\b",
    r"\b1099\b",
    r"\bw2 contract\b",
    r"\bfreelance\b",
    r"\btemporary\b",
    r"\btemp\b",
    r"\bfixed-term\b",
    r"\bfixed term\b",
    r"\bconsultant\b",
    r"\bcontingent\b",
    r"\bsubcontractor\b",
]

FULL_TIME_PATTERNS = [
    r"\bfull[- ]time\b",
    r"\bpermanent\b",
    r"\bdirect hire\b",
    r"\bregular\b",
    r"\bsalaried\b",
    r"\bfte\b",
]

COMPILED_CONTRACT_REGEX = [
    re.compile(p, re.IGNORECASE) for p in CONTRACT_PATTERNS
]
COMPILED_FULL_TIME_REGEX = [
    re.compile(p, re.IGNORECASE) for p in FULL_TIME_PATTERNS
]


def classify_employment_type(
    title: str,
    description: str = "",
    source_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Classifies a job posting into either 'FULL_TIME' or 'CONTRACT'.
    Follows the system flow diagram:
      Classify Employment Type -> Full-Time Jobs vs Contract Jobs

    Checks:
    1. Explicit source metadata (e.g. commitment, workplace_type, employment_type)
    2. Job Title keywords (e.g. "Software Engineer (Contract)")
    3. Job Description patterns
    Default: 'FULL_TIME' (standard industry corporate listing default).
    """
    metadata = source_metadata or {}

    # 1. Check metadata fields commonly provided by ATS systems
    meta_values = [
        str(metadata.get("commitment", "")).lower(),
        str(metadata.get("employment_type", "")).lower(),
        str(metadata.get("type", "")).lower(),
        str(metadata.get("schedule", "")).lower(),
    ]
    meta_text = " ".join(meta_values)

    for rx in COMPILED_CONTRACT_REGEX:
        if rx.search(meta_text):
            return "CONTRACT"

    for rx in COMPILED_FULL_TIME_REGEX:
        if rx.search(meta_text):
            return "FULL_TIME"

    # 2. Check Job Title
    for rx in COMPILED_CONTRACT_REGEX:
        if rx.search(title):
            return "CONTRACT"

    for rx in COMPILED_FULL_TIME_REGEX:
        if rx.search(title):
            return "FULL_TIME"

    # 3. Check first 800 characters of description
    desc_sample = description[:800]
    for rx in COMPILED_CONTRACT_REGEX:
        if rx.search(desc_sample):
            return "CONTRACT"

    # 4. Default standard posting to FULL_TIME
    return "FULL_TIME"

