import re
from typing import Dict, Any, Optional, Tuple

# Comprehensive Industry Signature Vocabularies aligned with the 7 Target Industries:
INDUSTRY_SIGNATURES = {
    "IT, Software & Technology": [
        r"\bsoftware\b", r"\bsaas\b", r"\bb2b\b", r"\bdeveloper tools\b",
        r"\bcloud infrastructure\b", r"\bapi\b", r"\bplatform\b", r"\bdevops\b",
        r"\bfrontend\b", r"\bbackend\b", r"\bfullstack\b", r"\bcybersecurity\b",
        r"\binfosec\b", r"\bcloud\b", r"\bkubernetes\b", r"\bmicroservices\b",
    ],
    "Healthcare": [
        r"\bclinical\b", r"\bpatient\b", r"\bhospital\b", r"\bhipaa\b",
        r"\bhealthcare\b", r"\bmedical\b", r"\bmedicine\b", r"\behr\b",
        r"\bemr\b", r"\btelehealth\b", r"\bdoctor\b", r"\bphysician\b",
        r"\bhealth tech\b", r"\bhealthtech\b", r"\bcare\b", r"\bdiagnostic\b",
    ],
    "Finance & Banking": [
        r"\bfintech\b", r"\bbanking\b", r"\bpayments?\b", r"\bledger\b",
        r"\bcrypto\b", r"\bblockchain\b", r"\bwallet\b", r"\btrading\b",
        r"\bsec\b", r"\bcompliance\b", r"\bcredit\b", r"\bloan\b",
        r"\bequity\b", r"\bportfolio\b", r"\bhedge fund\b", r"\bwealth management\b",
        r"\bsecurities\b", r"\btransactions?\b", r"\bfinancial\b", r"\bbank\b",
    ],
    "Insurance": [
        r"\binsurance\b", r"\binsurtech\b", r"\bpolicyholder\b", r"\bunderwriting\b",
        r"\bunderwriter\b", r"\bactuarial\b", r"\bactuary\b", r"\bclaims\b",
        r"\bpremium\b", r"\breinsurance\b", r"\bcoverage\b", r"\bpolicy\b",
        r"\blife insurance\b", r"\bproperty\b", r"\bcasualty\b",
    ],
    "Solar, Energy & Utilities": [
        r"\benergy\b", r"\bsolar\b", r"\bcleantech\b", r"\bclean tech\b",
        r"\brenewable\b", r"\bbatter(y|ies)\b", r"\bpower grid\b",
        r"\bev charging\b", r"\bkilowatt\b", r"\bdecarbonization\b",
        r"\bclean energy\b", r"\belectricit(y|ies)\b", r"\bwind turbine\b",
        r"\bclimate tech\b", r"\butilities\b", r"\bpower generation\b", r"\bgrid\b",
    ],
    "Aerospace & Defense": [
        r"\bdefense\b", r"\baerospace\b", r"\bavionics\b", r"\bradar\b",
        r"\bmissiles?\b", r"\bsatellites?\b", r"\bsecurity clearance\b",
        r"\bsecret clearance\b", r"\bts/sci\b", r"\buav\b", r"\bdrones?\b",
        r"\bdod\b", r"\bnational security\b", r"\bweapon\b", r"\bunmanned\b",
        r"\bspacecraft\b", r"\bairforce\b", r"\bnavy\b", r"\bmilitary\b",
    ],
    "Pharma & Biotechnology": [
        r"\bpharma\b", r"\bpharmaceuticals?\b", r"\bbiotech\b", r"\bbiotechnology\b",
        r"\btherapeutics\b", r"\boncology\b", r"\bgenomics\b", r"\bfda\b",
        r"\bdrug discovery\b", r"\bclinical trials?\b", r"\bassays?\b", r"\bmolecular\b",
        r"\bbiolog(y|ical)\b", r"\bbiochemistry\b", r"\bmrna\b", r"\bvaccines?\b",
    ],
}

# Compiled regex for industry matching
COMPILED_INDUSTRY_REGEX = {
    ind: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for ind, patterns in INDUSTRY_SIGNATURES.items()
}

# Tech Role Signature Vocabularies
TECH_ROLE_SIGNATURES = [
    (
        "AI / Machine Learning Engineer",
        [
            r"\bai engineer\b", r"\bmachine learning\b", r"\bml engineer\b",
            r"\bdeep learning\b", r"\bllm\b", r"\bpytorch\b", r"\btensorflow\b",
            r"\bnlp\b", r"\bcomputer vision\b", r"\bgenai\b", r"\bgenerative ai\b",
        ],
    ),
    (
        "Data Engineer",
        [
            r"\bdata engineer\b", r"\betl\b", r"\bdata pipeline\b", r"\bsnowflake\b",
            r"\bdatabricks\b", r"\bspark\b", r"\bairflow\b", r"\bdbt\b",
            r"\bbigquery\b", r"\bdata warehouse\b",
        ],
    ),
    (
        "Data Scientist / Analyst",
        [
            r"\bdata scientist\b", r"\bdata analyst\b", r"\bbusiness intelligence analyst\b",
            r"\bdata analytics\b", r"\bstatistics\b", r"\ba/b testing\b",
        ],
    ),
    (
        "DevOps / SRE / Platform Engineer",
        [
            r"\bdevops\b", r"\bsre\b", r"\bsite reliability\b", r"\bplatform engineer\b",
            r"\bkubernetes\b", r"\bterraform\b", r"\bcloud infrastructure\b",
            r"\binfrastructure engineer\b", r"\bci/cd\b",
        ],
    ),
    (
        "Cybersecurity / Security Engineer",
        [
            r"\bsecurity engineer\b", r"\bcybersecurity\b", r"\binfosec\b",
            r"\bappsec\b", r"\bpenetration\b", r"\bsoc analyst\b",
            r"\bthreat analyst\b",
        ],
    ),
    (
        "Frontend Engineer",
        [
            r"\bfrontend\b", r"\bfront-end\b", r"\breact\b", r"\bvue\b",
            r"\bangular\b", r"\bnext\.?js\b", r"\bui engineer\b",
            r"\bweb developer\b",
        ],
    ),
    (
        "Full Stack Engineer",
        [
            r"\bfull stack\b", r"\bfullstack\b", r"\bfull-stack\b",
        ],
    ),
    (
        "Backend Engineer",
        [
            r"\bbackend\b", r"\bback-end\b", r"\bapi engineer\b",
            r"\bmicroservices\b", r"\bpython developer\b", r"\bpython engineer\b",
            r"\bjava developer\b", r"\bgolang engineer\b", r"\bnode\.?js developer\b",
            r"\bserver-side\b",
        ],
    ),
    (
        "Mobile Developer",
        [
            r"\bmobile developer\b", r"\bios developer\b", r"\bandroid developer\b",
            r"\bswift\b", r"\bkotlin\b", r"\breact native\b", r"\bflutter\b",
        ],
    ),
    (
        "QA / Automation Engineer",
        [
            r"\bqa engineer\b", r"\bquality assurance\b", r"\bsdet\b",
            r"\btest automation\b", r"\bautomation engineer\b",
        ],
    ),
    (
        "Embedded / Firmware Engineer",
        [
            r"\bembedded engineer\b", r"\bfirmware engineer\b", r"\brtos\b",
            r"\bmicrocontroller\b", r"\bkernel developer\b",
        ],
    ),
    (
        "Engineering Leadership",
        [
            r"\bengineering manager\b", r"\bdirector of engineering\b",
            r"\bvp of engineering\b", r"\btech lead\b", r"\bhead of engineering\b",
        ],
    ),
]

COMPILED_ROLE_REGEX = [
    (role_name, [re.compile(pattern, re.IGNORECASE) for pattern in patterns])
    for role_name, patterns in TECH_ROLE_SIGNATURES
]

# Employment Type Patterns
CONTRACT_PATTERNS = [
    r"\bcontract\b", r"\bcontractor\b", r"\bc2c\b", r"\bcorp-to-corp\b",
    r"\bcorp to corp\b", r"\b1099\b", r"\bw2 contract\b", r"\bcontract[- ]to[- ]hire\b",
    r"\bcontract to hire\b", r"\bc2h\b", r"\bfreelance\b", r"\btemporary\b",
    r"\btemp\b", r"\btemp[- ]to[- ]perm\b", r"\btemporary to permanent\b",
    r"\bfixed[- ]term\b", r"\bfixed term\b", r"\bconsultant\b", r"\bcontingent\b",
    r"\bcontingent worker\b", r"\bsubcontractor\b", r"\bhourly contract\b",
    r"\b\d+[- ]months?\s+contract\b", r"\b\d+[- ]years?\s+contract\b",
    r"\bcontract\s+(?:role|position|opportunity|basis|assignment|duration|engagement)\b",
]

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
]

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

PART_TIME_PATTERNS = [
    r"\bpart[- ]time\b", r"\bpart time\b", r"\b20 hours\b", r"\bhalf-time\b",
]

INTERN_PATTERNS = [
    r"\bintern\b", r"\binternship\b", r"\bco-op\b", r"\bstudent trainee\b",
]

FULL_TIME_PATTERNS = [
    r"\bfull[- ]time\b", r"\bpermanent\b", r"\bdirect hire\b", r"\bregular\b",
    r"\bsalaried\b", r"\bfte\b",
]

FT_OVERRIDE_PATTERNS = [
    r"(?i)\bthe\s+position\s+is\s+full[- ]time\b",
    r"(?i)\bthis\s+is\s+a\s+full[- ]time\b",
    r"(?i)\bfor\s+this\s+full[- ]time\b",
    r"(?i)\bfull[- ]time\s+(?:position|role|salaried|employment)\b",
    r"(?i)\bemployment\s+type\s*:\s*full[- ]time\b",
    r"(?i)\bjob\s+type\s*:\s*full[- ]time\b",
]

RX_CONTRACT = [re.compile(p, re.IGNORECASE) for p in CONTRACT_PATTERNS]
RX_CONTRACT_DESC = [re.compile(p, re.IGNORECASE) for p in CONTRACT_DESC_PATTERNS]
RX_DISCLAIMER = [re.compile(p, re.IGNORECASE) for p in DISCLAIMER_PATTERNS]
RX_PART_TIME = [re.compile(p, re.IGNORECASE) for p in PART_TIME_PATTERNS]
RX_INTERN = [re.compile(p, re.IGNORECASE) for p in INTERN_PATTERNS]
RX_FULL_TIME = [re.compile(p, re.IGNORECASE) for p in FULL_TIME_PATTERNS]
RX_FT_OVERRIDE = [re.compile(p, re.IGNORECASE) for p in FT_OVERRIDE_PATTERNS]


class JDAnalyzer:
    """
    Analyzes full Job Descriptions (JD) to deduce:
    1. Industry Classification (Healthcare, Finance, Defense, Energy, IT, etc.)
    2. Specific Tech Role (Backend, Frontend, Full Stack, DevOps, AI/ML, Data Engineer, etc.)
    3. Employment Type (FULL_TIME, CONTRACT, PART_TIME, INTERNSHIP)
    """

    @staticmethod
    def deduce_industry_from_jd(
        title: str,
        description: str,
        company_name: str = "",
        fallback_industry: Optional[str] = None,
    ) -> str:
        """
        Analyzes the JD text, company name, and title to deduce the industry domain.
        Returns one of:
          - 'Healthcare & Life Sciences'
          - 'Finance & FinTech'
          - 'Defense & Aerospace'
          - 'Energy & CleanTech'
          - 'Cybersecurity'
          - 'E-Commerce & Retail'
          - 'Information Technology'
        """
        text = f"{company_name} {title} {description}".lower()

        scores: Dict[str, int] = {}
        for ind, regex_list in COMPILED_INDUSTRY_REGEX.items():
            count = 0
            for rx in regex_list:
                matches = rx.findall(text)
                count += len(matches)
            scores[ind] = count

        # Find industry with highest score
        best_industry, highest_score = max(scores.items(), key=lambda item: item[1])

        # Require a minimal threshold score of 2 matches to override fallback
        if highest_score >= 2:
            return best_industry

        if fallback_industry and fallback_industry.strip() and fallback_industry.upper() != "ALL":
            return fallback_industry.strip()

        return best_industry if highest_score > 0 else "IT, Software & Technology"

    @staticmethod
    def deduce_tech_role_from_jd(title: str, description: str) -> str:
        """
        Analyzes title (highest weight) and JD description to pinpoint the exact Tech Role.
        """
        # 1. First check title match (highest precision)
        for role_name, regex_list in COMPILED_ROLE_REGEX:
            for rx in regex_list:
                if rx.search(title):
                    return role_name

        # 2. Check full text (title + description snippet)
        combined = f"{title} {description[:1200]}"
        scores = {}
        for role_name, regex_list in COMPILED_ROLE_REGEX:
            score = sum(len(rx.findall(combined)) for rx in regex_list)
            scores[role_name] = score

        best_role, top_score = max(scores.items(), key=lambda item: item[1])
        if top_score > 0:
            return best_role

        # Default fallback
        if "engineer" in title.lower() or "developer" in title.lower():
            return "Software Engineer"
        return "Technology Specialist"

    @staticmethod
    def deduce_employment_type_from_jd(
        title: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Deduces whether the position is 'FULL_TIME', 'CONTRACT', 'PART_TIME', or 'INTERNSHIP'
        based on the Job Description, title, and source metadata.
        """
        meta = metadata or {}
        meta_str = " ".join([
            str(meta.get("commitment", "")),
            str(meta.get("employment_type", "")),
            str(meta.get("type", "")),
        ])

        # 1. Internship (check title and metadata)
        for rx in RX_INTERN:
            if rx.search(title) or rx.search(meta_str):
                return "INTERNSHIP"

        # 2. Contract: check title and metadata directly
        for rx in RX_CONTRACT:
            if rx.search(title) or rx.search(meta_str):
                return "CONTRACT"

        # 3. Clean description of standard EEO/HR disclaimers
        clean_desc = description
        for d_rx in RX_DISCLAIMER:
            clean_desc = d_rx.sub(" ", clean_desc)

        # 4. Check Explicit Full-Time Override in Description (e.g. "The position is full-time")
        # If the employer explicitly states the role is full-time, casual mentions of "contract"
        # (such as managing vendor contracts, contract manufacturing, or client contracts) do not make it a contract job.
        for rx in RX_FT_OVERRIDE:
            if rx.search(clean_desc):
                return "FULL_TIME"

        # 5. Check high-precision contract section patterns across full description
        for rx in RX_CONTRACT_DESC:
            if rx.search(clean_desc):
                return "CONTRACT"

        # 6. Part-Time
        for rx in RX_PART_TIME:
            if rx.search(title) or rx.search(meta_str) or rx.search(clean_desc[:1200]):
                return "PART_TIME"

        # 7. Full-Time
        for rx in RX_FULL_TIME:
            if rx.search(title) or rx.search(meta_str) or rx.search(clean_desc[:1200]):
                return "FULL_TIME"

        # Default standard corporate role
        return "FULL_TIME"

