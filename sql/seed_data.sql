-- Seed Data for Companies across Industries
-- Verified live ATS job boards for Greenhouse, Lever, Ashby, and Generic HTML

-- 1. Information Technology
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('GitLab', 'gitlab.com', 'https://about.gitlab.com/jobs', 'Information Technology', TRUE),
('Figma', 'figma.com', 'https://www.figma.com/careers', 'Information Technology', TRUE),
('Datadog', 'datadoghq.com', 'https://www.datadoghq.com/careers', 'Information Technology', TRUE),
('Elastic', 'elastic.co', 'https://www.elastic.co/about/careers', 'Information Technology', TRUE),
('Linear', 'linear.app', 'https://linear.app/careers', 'Information Technology', TRUE),
('Synthesia', 'synthesia.io', 'https://www.synthesia.io/careers', 'Information Technology', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 2. Finance / FinTech
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('Robinhood', 'robinhood.com', 'https://robinhood.com/careers', 'Finance', TRUE),
('Coinbase', 'coinbase.com', 'https://www.coinbase.com/careers', 'Finance', TRUE),
('Ramp', 'ramp.com', 'https://ramp.com/careers', 'Finance', TRUE),
('Wealthfront', 'wealthfront.com', 'https://www.wealthfront.com/careers', 'Finance', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 3. Healthcare / HealthTech
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('Oscar Health', 'hioscar.com', 'https://www.hioscar.com/careers', 'Healthcare', TRUE),
('Doximity', 'doximity.com', 'https://www.doximity.com/careers', 'Healthcare', TRUE),
('Komodo Health', 'komodohealth.com', 'https://www.komodohealth.com/careers', 'Healthcare', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 4. Energy / CleanTech
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('ChargePoint', 'chargepoint.com', 'https://www.chargepoint.com/careers', 'Energy', TRUE),
('Palmetto', 'palmetto.com', 'https://palmetto.com/careers', 'Energy', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 5. Defense / Aerospace
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('Anduril Industries', 'anduril.com', 'https://www.anduril.com/careers', 'Defense', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;


-- Remove outdated invalid sources if any
DELETE FROM job_sources WHERE source_url LIKE '%boards/docker%' OR source_url LIKE '%boards/formenergy%' OR source_url LIKE '%boards/ro%' OR source_url LIKE '%boards/tempus%' OR source_url LIKE '%boards/brex%' OR source_url LIKE '%boards/span%' OR source_url LIKE '%ashbyhq.com/posting-api/job-board/vercel';

-- Re-populate job sources
-- GitLab (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/gitlab/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'GitLab'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Figma (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/figma/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Figma'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Datadog (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/datadog/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Datadog'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Elastic (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/elastic/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Elastic'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Linear (Ashby)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://api.ashbyhq.com/posting-api/job-board/linear', 'ashby', TRUE
FROM companies WHERE name = 'Linear'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Synthesia (Ashby)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://api.ashbyhq.com/posting-api/job-board/synthesia', 'ashby', TRUE
FROM companies WHERE name = 'Synthesia'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Robinhood (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/robinhood/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Robinhood'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Coinbase (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/coinbase/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Coinbase'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Ramp (Ashby)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://api.ashbyhq.com/posting-api/job-board/ramp', 'ashby', TRUE
FROM companies WHERE name = 'Ramp'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Wealthfront (Lever)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://api.lever.co/v0/postings/wealthfront?mode=json', 'lever', TRUE
FROM companies WHERE name = 'Wealthfront'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Oscar Health (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/oscar/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Oscar Health'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Doximity (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/doximity/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Doximity'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Komodo Health (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/komodohealth/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Komodo Health'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- ChargePoint (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/chargepoint/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'ChargePoint'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Palmetto (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/palmetto/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Palmetto'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);

-- Anduril Industries (Greenhouse)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, 'https://boards-api.greenhouse.io/v1/boards/andurilindustries/jobs?content=true', 'greenhouse', TRUE
FROM companies WHERE name = 'Anduril Industries'
AND NOT EXISTS (SELECT 1 FROM job_sources WHERE company_id = companies.id);
