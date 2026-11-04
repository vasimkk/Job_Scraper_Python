-- Seed Data for Companies across Industries
-- Verified live career pages scraped directly via Playwright browser automation

-- 1. Information Technology
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('GitLab', 'gitlab.com', 'https://about.gitlab.com/jobs', 'Information Technology', TRUE),
('Figma', 'figma.com', 'https://www.figma.com/careers', 'Information Technology', TRUE),
('Datadog', 'datadoghq.com', 'https://www.datadoghq.com/careers', 'Information Technology', TRUE),
('Elastic', 'elastic.co', 'https://www.elastic.co/about/careers', 'Information Technology', TRUE),
('Linear', 'linear.app', 'https://linear.app/careers', 'Information Technology', TRUE),
('Synthesia', 'synthesia.io', 'https://www.synthesia.io/careers', 'Information Technology', TRUE),
('Vercel', 'vercel.com', 'https://vercel.com/careers', 'Information Technology', TRUE),
('Stripe', 'stripe.com', 'https://stripe.com/jobs', 'Information Technology', TRUE),
('GitHub', 'github.com', 'https://github.com/about/careers', 'Information Technology', TRUE),
('HashiCorp', 'hashicorp.com', 'https://www.hashicorp.com/careers', 'Information Technology', TRUE)
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
('Wealthfront', 'wealthfront.com', 'https://wealthfront.com/careers', 'Finance', TRUE),
('Plaid', 'plaid.com', 'https://plaid.com/careers', 'Finance', TRUE),
('Brex', 'brex.com', 'https://www.brex.com/careers', 'Finance', TRUE),
('Affirm', 'affirm.com', 'https://www.affirm.com/careers', 'Finance', TRUE),
('Block', 'block.xyz', 'https://block.xyz/careers', 'Finance', TRUE)
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
('Komodo Health', 'komodohealth.com', 'https://www.komodohealth.com/careers', 'Healthcare', TRUE),
('BetterHelp', 'betterhelp.com', 'https://www.betterhelp.com/careers/', 'Healthcare', TRUE),
('Wheel', 'wheel.com', 'https://www.wheel.com/careers', 'Healthcare', TRUE),
('Abby Care', 'abbycare.org', 'https://www.abbycare.org/careers', 'Healthcare', TRUE),
('Datavant', 'datavant.com', 'https://datavant.com/careers', 'Healthcare', TRUE),
('Ro', 'ro.co', 'https://ro.co/careers', 'Healthcare', TRUE),
('Tempus AI', 'tempus.com', 'https://www.tempus.com/careers/', 'Healthcare', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 4. Energy / CleanTech
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('ChargePoint', 'chargepoint.com', 'https://www.chargepoint.com/careers', 'Energy', TRUE),
('Palmetto', 'palmetto.com', 'https://palmetto.com/careers', 'Energy', TRUE),
('Sunrun', 'sunrun.com', 'https://careers.sunrun.com/', 'Energy', TRUE),
('Enphase Energy', 'enphase.com', 'https://enphase.com/careers', 'Energy', TRUE),
('Form Energy', 'formenergy.com', 'https://formenergy.com/careers', 'Energy', TRUE),
('Rivian', 'rivian.com', 'https://rivian.com/careers', 'Energy', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 5. Defense / Aerospace
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('Anduril Industries', 'anduril.com', 'https://www.anduril.com/careers', 'Defense', TRUE),
('Palantir Technologies', 'palantir.com', 'https://www.palantir.com/careers/', 'Defense', TRUE),
('SpaceX', 'spacex.com', 'https://www.spacex.com/careers/', 'Defense', TRUE),
('Planet Labs', 'planet.com', 'https://www.planet.com/careers/', 'Defense', TRUE),
('Astranis', 'astranis.com', 'https://www.astranis.com/careers', 'Defense', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- 6. Cybersecurity
INSERT INTO companies (name, domain, career_url, industry, active)
VALUES 
('CrowdStrike', 'crowdstrike.com', 'https://www.crowdstrike.com/careers/', 'Cybersecurity', TRUE),
('Cloudflare', 'cloudflare.com', 'https://www.cloudflare.com/careers/', 'Cybersecurity', TRUE),
('SentinelOne', 'sentinelone.com', 'https://www.sentinelone.com/careers/', 'Cybersecurity', TRUE),
('Zscaler', 'zscaler.com', 'https://www.zscaler.com/careers', 'Cybersecurity', TRUE),
('Snyk', 'snyk.io', 'https://snyk.io/careers/', 'Cybersecurity', TRUE)
ON CONFLICT (name) DO UPDATE SET 
    domain = EXCLUDED.domain,
    career_url = EXCLUDED.career_url,
    industry = EXCLUDED.industry,
    active = EXCLUDED.active;

-- Clean out any third party or non-career sources
DELETE FROM job_sources 
WHERE source_url LIKE '%boards-api.greenhouse.io%'
   OR source_url LIKE '%api.lever.co%'
   OR source_url LIKE '%api.ashbyhq.com%'
   OR scraper_type = 'feed_api'
   OR source_url LIKE '%jobicy.com%'
   OR source_url LIKE '%remotive.com%';

-- Direct Company Career Page Job Sources (Scraped directly via Playwright)
INSERT INTO job_sources (company_id, source_url, scraper_type, active)
SELECT id, career_url, 'playwright', TRUE
FROM companies
WHERE career_url IS NOT NULL
ON CONFLICT DO NOTHING;
