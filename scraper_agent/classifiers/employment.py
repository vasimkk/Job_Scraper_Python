import re
from typing import Optional, Dict, Any

# Regex patterns for contract employment
CONTRACT_PATTERNS = [
    r"\bcontract\b",
    r"\bcontractor\b",
    r"\bc2c\b",
    r"\bcorp-to-corp\b",
    r"\bcorp to corp\b",
    r"\b1099\b",
    r"\bw2 contract\b",
    r"\bcontract[- ]to[- ]hire\b",
    r"\bcontract to hire\b",
    r"\bc2h\b",
    r"\bfreelance\b",
    r"\bfreelancer\b",
    r"\btemporary\b",
    r"\btemp\b",
    r"\btemp[- ]to[- ]perm\b",
    r"\btemporary to permanent\b",
    r"\bfixed[- ]term\b",
    r"\bfixed term\b",
    r"\bconsultant\b",
    r"\bcontingent\b",
    r"\bcontingent worker\b",
    r"\bsubcontractor\b",
    r"\bhourly contract\b",
    r"\b\d+[- ]months?\s+contract\b",
    r"\b\d+[- ]years?\s+contract\b",
    r"\bcontract\s+(?:role|position|opportunity|basis|assignment|duration|engagement)\b",
]

# Patterns in JD description indicating contract status
CONTRACT_DESC_PATTERNS = [
    r"(?:job|employment|position|work|role)\s+type\s*:\s*.*?\b(?:contract|temporary|fixed[- ]term|fixed term|c2c|1099|c2h|contractor)\b",
    r"\bcontract[- ]to[- ]hire\b",
    r"\bc2h\b",
    r"\btemp[- ]to[- ]perm\b",
    r"\btemporary to permanent\b",
    r"\b\d+[- ]months?\s+contract\b",
    r"\b\d+[- ]years?\s+contract\b",
    r"\bcontract\s+(?:role|position|basis|opportunity|assignment|duration|engagement)\b",
    r"\b(?:w2|c2c|1099)\s+(?:contract|contractor|role|position|basis)\b",
    r"\bcorp[- ]to[- ]corp\b",
    r"\bfixed[- ]term\s+(?:contract|position|role|employment)\b",
    r"\bstatement of work\b",
]

# Standard HR / Legal / EEO disclaimer text that mentions "contractor" but is NOT a contract job
DISCLAIMER_PATTERNS = [
    r"(?i)\bfederal contractor\b",
    r"(?i)\bgovernment contractor\b",
    r"(?i)\baffirmative action\b.*?\bcontractor\b",
    r"(?i)\bemployment or an? (?:independent )?contractor role\b",
    r"(?i)\bapplicant or (?:independent )?contractor\b",
    r"(?i)\bemployee or (?:contingent worker|contractor)\b",
    r"(?i)\bformer employee or contractor\b",
    r"(?i)\bprevious employee or contractor\b",
    r"(?i)\bindependent contractor status under\b",
    r"(?i)\bdoes not constitute an? (?:employment )?contract\b",
]

# Explicit Full-Time declarations in JD that override casual mentions of "contract"
FT_OVERRIDE_PATTERNS = [
    r"(?i)\bthe\s+position\s+is\s+full[- ]time\b",
    r"(?i)\bthis\s+is\s+a\s+full[- ]time\b",
    r"(?i)\bfor\s+this\s+full[- ]time\b",
    r"(?i)\bfull[- ]time\s+(?:position|role|salaried|employment)\b",
    r"(?i)\bemployment\s+type\s*:\s*full[- ]time\b",
    r"(?i)\bjob\s+type\s*:\s*full[- ]time\b",
]

COMPILED_FT_OVERRIDE_REGEX = [
    re.compile(p, re.IGNORECASE) for p in FT_OVERRIDE_PATTERNS
]

COMPILED_CONTRACT_REGEX = [
    re.compile(p, re.IGNORECASE) for p in CONTRACT_PATTERNS
]
COMPILED_CONTRACT_DESC_REGEX = [
    re.compile(p, re.IGNORECASE) for p in CONTRACT_DESC_PATTERNS
]
COMPILED_DISCLAIMER_REGEX = [
    re.compile(p, re.IGNORECASE) for p in DISCLAIMER_PATTERNS
]
FULL_TIME_PATTERNS = [
    r"\bfull[- ]time\b",
    r"\bpermanent\b",
    r"\bdirect hire\b",
    r"\bregular\b",
    r"\bsalaried\b",
    r"\bfte\b",
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

    # 2. Check Job Title (highest priority for contract roles)
    for rx in COMPILED_CONTRACT_REGEX:
        if rx.search(title):
            return "CONTRACT"

    # 3. Clean Description of legal/EEO disclaimer text
    clean_desc = description
    for d_rx in COMPILED_DISCLAIMER_REGEX:
        clean_desc = d_rx.sub(" ", clean_desc)

    # 4. Check Explicit Full-Time Override in Description (e.g. "The position is full-time")
    # If the employer explicitly states the role is full-time, casual mentions of "contract"
    # (such as managing vendor contracts, contract manufacturing, or customer contracts) do not make it a contract job.
    for rx in COMPILED_FT_OVERRIDE_REGEX:
        if rx.search(clean_desc):
            return "FULL_TIME"

    # 5. Check high-precision contract section patterns in Description
    for rx in COMPILED_CONTRACT_DESC_REGEX:
        if rx.search(clean_desc):
            return "CONTRACT"

    # 6. Check generic full-time keywords in Title
    for rx in COMPILED_FULL_TIME_REGEX:
        if rx.search(title):
            return "FULL_TIME"

    # 7. Default standard corporate posting to FULL_TIME
    return "FULL_TIME"

