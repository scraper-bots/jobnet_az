-- Database schema for JobSearch.az scraper
-- Schema: weapply

CREATE SCHEMA IF NOT EXISTS weapply;

-- Main jobs table
CREATE TABLE IF NOT EXISTS weapply.jobs (
    id BIGINT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    is_new BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_vip BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE,
    deadline_at TIMESTAMP WITH TIME ZONE,
    salary_amount DECIMAL(10,2),
    salary_text VARCHAR(100),
    hide_company BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    phone VARCHAR(50),
    
    -- Company information
    company_id INTEGER,
    company_title VARCHAR(300),
    company_slug VARCHAR(300),
    company_logo TEXT,
    company_logo_mini TEXT,
    company_first_char CHAR(1),
    company_has_story BOOLEAN DEFAULT FALSE,
    company_summary TEXT,
    company_text TEXT,
    company_address TEXT,
    company_vacancy_count INTEGER DEFAULT 0,
    company_cover TEXT,
    
    -- Category information
    category_id INTEGER,
    category_title VARCHAR(200),
    category_image_mini TEXT,
    
    -- Job details
    text_content TEXT,
    text_content_clean TEXT,
    request_type VARCHAR(50),
    direct_apply BOOLEAN DEFAULT FALSE,
    apply_link TEXT,
    has_company_info BOOLEAN DEFAULT FALSE,
    
    -- Coordinates
    company_lat DECIMAL(10, 8),
    company_lng DECIMAL(11, 8),
    
    -- Metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT jobs_id_positive CHECK (id > 0)
);

-- Company phones table (one-to-many relationship)
CREATE TABLE IF NOT EXISTS weapply.company_phones (
    id SERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES weapply.jobs(id) ON DELETE CASCADE,
    phone VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Company websites table (one-to-many relationship)
CREATE TABLE IF NOT EXISTS weapply.company_websites (
    id SERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES weapply.jobs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Company emails table (one-to-many relationship)
CREATE TABLE IF NOT EXISTS weapply.company_emails (
    id SERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES weapply.jobs(id) ON DELETE CASCADE,
    email VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Company industries table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS weapply.company_industries (
    id SERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES weapply.jobs(id) ON DELETE CASCADE,
    industry_id INTEGER NOT NULL,
    industry_title VARCHAR(200) NOT NULL,
    industry_image_mini TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Company gallery table (one-to-many relationship)
CREATE TABLE IF NOT EXISTS weapply.company_gallery (
    id SERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES weapply.jobs(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    alt_text VARCHAR(300),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Job files table (one-to-many relationship)
CREATE TABLE IF NOT EXISTS weapply.job_files (
    id SERIAL PRIMARY KEY,
    job_id BIGINT REFERENCES weapply.jobs(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_name VARCHAR(300),
    file_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON weapply.jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON weapply.jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_category_id ON weapply.jobs(category_id);
CREATE INDEX IF NOT EXISTS idx_jobs_salary_amount ON weapply.jobs(salary_amount);
CREATE INDEX IF NOT EXISTS idx_jobs_is_new ON weapply.jobs(is_new);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON weapply.jobs(scraped_at);
CREATE INDEX IF NOT EXISTS idx_jobs_title_gin ON weapply.jobs USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_jobs_text_content_gin ON weapply.jobs USING gin(to_tsvector('english', text_content_clean));

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION weapply.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_jobs_updated_at ON weapply.jobs;
CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON weapply.jobs 
    FOR EACH ROW EXECUTE FUNCTION weapply.update_updated_at_column();