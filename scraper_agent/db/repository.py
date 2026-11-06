import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from scraper_agent.db.connection import get_dict_cursor, get_db_connection
from scraper_agent.models.job import Company, JobSource, ProcessedJob, ScrapeRunStats
from scraper_agent.embeddings.embedder import JobEmbedder

logger = logging.getLogger(__name__)


class JobRepository:
    """Repository handling all database operations for companies, sources, jobs, and scrape runs."""

    @staticmethod
    def get_or_create_company(
        name: str,
        domain: Optional[str] = None,
        career_url: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> Company:
        """
        Dynamically retrieves an existing company or creates a new record.
        Ensures dynamic company discovery without any hardcoded names.
        """
        clean_name = name.strip()
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, domain, career_url, industry, active, created_at, updated_at
                FROM companies
                WHERE LOWER(name) = LOWER(%s)
                """,
                (clean_name,),
            )
            row = cur.fetchone()
            if row:
                # Update missing fields if new info discovered
                comp = Company(**row)
                needs_update = False
                update_fields = []
                params = []
                if not comp.industry and industry:
                    update_fields.append("industry = %s")
                    params.append(industry)
                    needs_update = True
                if not comp.career_url and career_url:
                    update_fields.append("career_url = %s")
                    params.append(career_url)
                    needs_update = True
                if not comp.domain and domain:
                    update_fields.append("domain = %s")
                    params.append(domain)
                    needs_update = True

                if needs_update:
                    params.append(comp.id)
                    with get_db_connection() as conn:
                        with conn.cursor() as u_cur:
                            set_clause = ", ".join(update_fields)
                            u_cur.execute(
                                f"UPDATE companies SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                                params,
                            )
                return comp

        # Insert new company
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO companies (name, domain, career_url, industry, active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    RETURNING id, name, domain, career_url, industry, active, created_at, updated_at
                    """,
                    (clean_name, domain, career_url, industry),
                )
                r = cur.fetchone()
                return Company(
                    id=r[0],
                    name=r[1],
                    domain=r[2],
                    career_url=r[3],
                    industry=r[4],
                    active=r[5],
                    created_at=r[6],
                    updated_at=r[7],
                )

    @staticmethod
    def get_or_create_job_source(
        company_id: int, source_url: str, scraper_type: str
    ) -> JobSource:
        """
        Dynamically retrieves or creates a job source for a company.
        """
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT id, company_id, source_url, scraper_type, active,
                       last_run_at, last_success_at, last_failure_at, created_at, updated_at
                FROM job_sources
                WHERE company_id = %s AND source_url = %s
                """,
                (company_id, source_url),
            )
            row = cur.fetchone()
            if row:
                return JobSource(**row)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_sources (company_id, source_url, scraper_type, active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id, company_id, source_url, scraper_type, active,
                              last_run_at, last_success_at, last_failure_at, created_at, updated_at
                    """,
                    (company_id, source_url, scraper_type),
                )
                r = cur.fetchone()
                return JobSource(
                    id=r[0],
                    company_id=r[1],
                    source_url=r[2],
                    scraper_type=r[3],
                    active=r[4],
                    last_run_at=r[5],
                    last_success_at=r[6],
                    last_failure_at=r[7],
                    created_at=r[8],
                    updated_at=r[9],
                )

    @staticmethod
    def get_distinct_industries() -> List[str]:
        """Fetch all unique industries present in the companies table."""
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT industry 
                FROM companies 
                WHERE industry IS NOT NULL AND active = TRUE
                ORDER BY industry ASC
                """
            )
            rows = cur.fetchall()
            return [row["industry"] for row in rows]

    @staticmethod
    def get_companies_by_industry(industry: Optional[str] = None) -> List[Company]:
        """Fetch active companies, optionally filtered by industry."""
        with get_dict_cursor() as cur:
            if industry and industry.upper() != "ALL":
                cur.execute(
                    """
                    SELECT id, name, domain, career_url, industry, active, created_at, updated_at
                    FROM companies
                    WHERE active = TRUE AND LOWER(industry) = LOWER(%s)
                    ORDER BY name ASC
                    """,
                    (industry,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, domain, career_url, industry, active, created_at, updated_at
                    FROM companies
                    WHERE active = TRUE
                    ORDER BY industry ASC, name ASC
                    """
                )
            rows = cur.fetchall()
            return [Company(**row) for row in rows]

    @staticmethod
    def get_company_by_name(name: str) -> Optional[Company]:
        """Retrieve a company by its name."""
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, domain, career_url, industry, active, created_at, updated_at
                FROM companies
                WHERE LOWER(name) = LOWER(%s)
                """,
                (name,),
            )
            row = cur.fetchone()
            return Company(**row) if row else None

    @staticmethod
    def check_existing_jobs(
        company_id: int, external_job_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Flow Step 6: Checks PostgreSQL database for already stored jobs matching external_job_ids.
        Returns a dictionary mapping external_job_id -> row data.
        """
        if not external_job_ids:
            return {}
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT id, external_job_id, content_hash, status, employment_type, tech_role, first_seen_at, last_seen_at
                FROM jobs
                WHERE company_id = %s AND external_job_id = ANY(%s)
                """,
                (company_id, external_job_ids),
            )
            rows = cur.fetchall()
            return {r["external_job_id"]: r for r in rows}

    @staticmethod
    def get_company_by_id(company_id: int) -> Optional[Company]:
        """Retrieve a company by its ID."""
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, domain, career_url, industry, active, created_at, updated_at
                FROM companies
                WHERE id = %s
                """,
                (company_id,),
            )
            row = cur.fetchone()
            return Company(**row) if row else None

    @staticmethod
    def get_active_sources_for_company(company_id: int) -> List[JobSource]:
        """Fetch active job sources for a given company."""
        with get_dict_cursor() as cur:
            cur.execute(
                """
                SELECT id, company_id, source_url, scraper_type, active,
                       last_run_at, last_success_at, last_failure_at, created_at, updated_at
                FROM job_sources
                WHERE company_id = %s AND active = TRUE
                ORDER BY id ASC
                """,
                (company_id,),
            )
            rows = cur.fetchall()
            return [JobSource(**row) for row in rows]

    @staticmethod
    def upsert_job(job: ProcessedJob) -> str:
        """
        Inserts or updates a single job post in the database.
        Returns:
            'NEW': Fresh job inserted
            'UPDATED': Existing job content changed
            'DUPLICATE': Unchanged job (last_seen_at updated)
            'INVALID': Data validation failed
        """
        if not job.title or not job.job_url or not job.external_job_id:
            return "INVALID"

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return JobRepository._upsert_job_with_cursor(cur, job)

    @staticmethod
    def _upsert_job_with_cursor(cur, job: ProcessedJob) -> str:
        """Internal helper to upsert a job using an active cursor."""
        if not job.title or not job.job_url or not job.external_job_id:
            return "INVALID"

        embedding_str = JobEmbedder.vector_to_pg_string(job.job_embedding)

        # Check if job already exists
        cur.execute(
            """
            SELECT id, content_hash 
            FROM jobs 
            WHERE company_id = %s AND external_job_id = %s
            """,
            (job.company_id, job.external_job_id),
        )
        existing = cur.fetchone()

        if not existing:
            # New Job
            cur.execute(
                """
                INSERT INTO jobs (
                    company_id, source_id, external_job_id, title, description,
                    location, city, state, country, remote_type, employment_type,
                    tech_role, posted_at, source_updated_at, first_seen_at, last_seen_at,
                    job_url, application_url, content_hash, status, job_embedding
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                    %s, %s, %s, %s, %s::vector
                )
                """,
                (
                    job.company_id,
                    job.source_id,
                    job.external_job_id,
                    job.title,
                    job.description,
                    job.location,
                    job.city,
                    job.state,
                    job.country,
                    job.remote_type,
                    job.employment_type,
                    job.tech_role,
                    job.posted_at,
                    job.source_updated_at,
                    job.job_url,
                    job.application_url,
                    job.content_hash,
                    job.status,
                    embedding_str,
                ),
            )
            return "NEW"

        job_id, existing_hash = existing
        if existing_hash != job.content_hash:
            # Content updated
            cur.execute(
                """
                UPDATE jobs SET
                    source_id = %s,
                    title = %s,
                    description = %s,
                    location = %s,
                    city = %s,
                    state = %s,
                    country = %s,
                    remote_type = %s,
                    employment_type = %s,
                    tech_role = %s,
                    posted_at = COALESCE(%s, posted_at),
                    source_updated_at = COALESCE(%s, source_updated_at),
                    job_url = %s,
                    application_url = %s,
                    content_hash = %s,
                    job_embedding = COALESCE(%s::vector, job_embedding),
                    status = 'OPEN',
                    last_seen_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    job.source_id,
                    job.title,
                    job.description,
                    job.location,
                    job.city,
                    job.state,
                    job.country,
                    job.remote_type,
                    job.employment_type,
                    job.tech_role,
                    job.posted_at,
                    job.source_updated_at,
                    job.job_url,
                    job.application_url,
                    job.content_hash,
                    embedding_str,
                    job_id,
                ),
            )
            return "UPDATED"
        else:
            # Duplicate (Content unchanged, touch last_seen_at)
            if embedding_str:
                cur.execute(
                    """
                    UPDATE jobs SET
                        last_seen_at = CURRENT_TIMESTAMP,
                        status = 'OPEN',
                        job_embedding = COALESCE(job_embedding, %s::vector)
                    WHERE id = %s
                    """,
                    (embedding_str, job_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE jobs SET
                        last_seen_at = CURRENT_TIMESTAMP,
                        status = 'OPEN'
                    WHERE id = %s
                    """,
                    (job_id,),
                )
            return "DUPLICATE"

    @staticmethod
    def upsert_jobs_batch(jobs: List[ProcessedJob]) -> Tuple[int, int, int, int]:
        """
        Efficiently upserts a list of jobs reusing a single connection and transaction.
        Returns: (new_count, updated_count, duplicate_count, invalid_count)
        """
        new_cnt = updated_cnt = duplicate_cnt = invalid_cnt = 0
        if not jobs:
            return 0, 0, 0, 0

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for job in jobs:
                    res = JobRepository._upsert_job_with_cursor(cur, job)
                    if res == "NEW":
                        new_cnt += 1
                    elif res == "UPDATED":
                        updated_cnt += 1
                    elif res == "DUPLICATE":
                        duplicate_cnt += 1
                    elif res == "INVALID":
                        invalid_cnt += 1

        return new_cnt, updated_cnt, duplicate_cnt, invalid_cnt

    @staticmethod
    def start_scrape_run(source_id: int) -> int:
        """Create a new scrape_runs entry and return its ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO scrape_runs (source_id, started_at, status)
                    VALUES (%s, CURRENT_TIMESTAMP, 'PENDING')
                    RETURNING id
                    """,
                    (source_id,),
                )
                run_id = cur.fetchone()[0]
                return run_id

    @staticmethod
    def complete_scrape_run(run_id: int, stats: ScrapeRunStats) -> None:
        """Update scrape_runs with final metrics."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE scrape_runs SET
                        completed_at = CURRENT_TIMESTAMP,
                        jobs_found = %s,
                        new_jobs = %s,
                        updated_jobs = %s,
                        duplicate_jobs = %s,
                        invalid_jobs = %s,
                        status = %s,
                        error_message = %s
                    WHERE id = %s
                    """,
                    (
                        stats.jobs_found,
                        stats.new_jobs,
                        stats.updated_jobs,
                        stats.duplicate_jobs,
                        stats.invalid_jobs,
                        stats.status,
                        stats.error_message,
                        run_id,
                    ),
                )

    @staticmethod
    def update_job_source_status(source_id: int, success: bool) -> None:
        """Update job_sources timestamps following a run."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if success:
                    cur.execute(
                        """
                        UPDATE job_sources SET
                            last_run_at = CURRENT_TIMESTAMP,
                            last_success_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (source_id,),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE job_sources SET
                            last_run_at = CURRENT_TIMESTAMP,
                            last_failure_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (source_id,),
                    )

    @staticmethod
    def get_dashboard_summary() -> Dict[str, Any]:
        """Aggregate statistical summary for reporting."""
        with get_dict_cursor() as cur:
            # Total counts
            cur.execute("SELECT count(*) as count FROM companies;")
            total_companies = cur.fetchone()["count"]

            cur.execute("SELECT count(*) as count FROM job_sources WHERE active = TRUE;")
            active_sources = cur.fetchone()["count"]

            cur.execute("SELECT count(*) as count FROM jobs;")
            total_jobs = cur.fetchone()["count"]

            # Jobs by industry
            cur.execute(
                """
                SELECT c.industry, count(j.id) as job_count
                FROM companies c
                LEFT JOIN jobs j ON c.id = j.company_id
                GROUP BY c.industry
                ORDER BY job_count DESC;
                """
            )
            industry_counts = cur.fetchall()

            # Jobs by employment_type
            cur.execute(
                """
                SELECT COALESCE(employment_type, 'UNKNOWN') as emp_type, count(*) as count
                FROM jobs
                GROUP BY employment_type
                ORDER BY count DESC;
                """
            )
            employment_counts = cur.fetchall()

            # Jobs by remote_type
            cur.execute(
                """
                SELECT COALESCE(remote_type, 'UNKNOWN') as remote_type, count(*) as count
                FROM jobs
                GROUP BY remote_type
                ORDER BY count DESC;
                """
            )
            remote_counts = cur.fetchall()

            # Jobs by tech_role
            cur.execute(
                """
                SELECT COALESCE(tech_role, 'Unclassified') as tech_role, count(*) as count
                FROM jobs
                GROUP BY tech_role
                ORDER BY count DESC;
                """
            )
            tech_role_counts = cur.fetchall()

            return {
                "total_companies": total_companies,
                "active_sources": active_sources,
                "total_jobs": total_jobs,
                "by_industry": industry_counts,
                "by_employment_type": employment_counts,
                "by_remote_type": remote_counts,
                "by_tech_role": tech_role_counts,
            }
