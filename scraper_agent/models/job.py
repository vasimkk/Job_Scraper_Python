from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Company:
    id: int
    name: str
    domain: Optional[str]
    career_url: Optional[str]
    industry: Optional[str]
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class JobSource:
    id: int
    company_id: int
    source_url: str
    scraper_type: str
    active: bool = True
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RawJobPost:
    """Raw job post directly from ATS/Career source."""
    external_job_id: str
    title: str
    raw_description: str
    raw_location: str
    job_url: str
    application_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedJob:
    """Fully parsed, classified, and normalized job ready for DB storage."""
    company_id: int
    source_id: int
    external_job_id: str
    title: str
    description: str
    location: str
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    remote_type: str  # 'REMOTE', 'HYBRID', 'ON_SITE', 'UNKNOWN'
    employment_type: str  # 'FULL_TIME', 'CONTRACT', 'PART_TIME', 'INTERNSHIP'
    posted_at: Optional[datetime]
    source_updated_at: Optional[datetime]
    job_url: str
    application_url: Optional[str]
    content_hash: str
    is_tech: bool
    tech_role: Optional[str] = "Software Engineer"
    tech_keywords: List[str] = field(default_factory=list)
    status: str = "OPEN"
    job_embedding: Optional[List[float]] = None


@dataclass
class ScrapeRunStats:
    source_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    jobs_found: int = 0
    new_jobs: int = 0
    updated_jobs: int = 0
    duplicate_jobs: int = 0
    invalid_jobs: int = 0
    status: str = "PENDING"  # 'SUCCESS', 'FAILED', 'PARTIAL'
    error_message: Optional[str] = None

