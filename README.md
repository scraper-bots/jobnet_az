# JobSearch.az Scraper

A comprehensive scraper for JobSearch.az that fetches all job listings with detailed information and saves them to a PostgreSQL database.

## Features

- Scrapes all job listings from JobSearch.az API
- Fetches detailed job information for each listing
- Handles pagination automatically
- Cleans HTML content from job descriptions
- Stores data in PostgreSQL with proper schema
- Handles rate limiting and request delays
- Comprehensive error handling and logging
- Supports both full scraping and specific job scraping

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in `.env`:
```
PGUSER=your_db_user
PGPASSWORD=your_db_password
PGHOST=your_db_host
PGPORT=5432
PGDATABASE=your_db_name
PGSSLMODE=require
PGCHANNELBINDING=require
```

3. Set up the database schema:
```bash
python main.py --setup-only
```

## Usage

### Scrape All Jobs
```bash
# Scrape all available jobs
python main.py

# Scrape with custom delay range (2-5 seconds between requests)
python main.py --delay-min 2 --delay-max 5

# Scrape only first 5 pages
python main.py --max-pages 5
```

### Test Mode
```bash
# Test with only the first page
python main.py --test
```

### Scrape Specific Jobs
```bash
# Scrape specific jobs by their slugs
python main.py --slugs "company-job-title-123456" "another-company-job-789"
```

## Database Schema

The scraper creates the following tables in the `weapply` schema:

- `jobs` - Main job information
- `company_phones` - Company phone numbers
- `company_websites` - Company websites
- `company_emails` - Company email addresses
- `company_industries` - Company industries
- `company_gallery` - Company gallery images
- `job_files` - Job-related files

## API Details

The scraper uses the JobSearch.az API endpoints:

1. **Jobs List API**: `GET /api-az/vacancies-az`
   - Returns paginated job listings
   - Supports pagination with `ignore` and `ignore_hash` parameters

2. **Job Details API**: `GET /api-az/vacancies-az/{slug}`
   - Returns detailed information for a specific job
   - Requires the job slug from the listings

## Data Processing

- HTML content is cleaned and converted to plain text
- Salary information is parsed and stored both as numeric values and original text
- View counts with 'K' suffix are converted to actual numbers
- Phone numbers are formatted and cleaned
- Company coordinates are extracted and stored separately

## Logging

The scraper creates detailed logs with timestamps showing:
- Progress of scraping operations
- Success/failure of individual job saves
- Database operations
- Error messages and warnings

Logs are saved to files with format: `scraper_YYYYMMDD_HHMMSS.log`

## Error Handling

- Automatic retry logic for failed API requests
- Database transaction rollback on errors
- Validation of job data before saving
- Graceful handling of missing or malformed data
- Comprehensive error logging

## Rate Limiting

The scraper includes built-in delays between requests:
- Default: 2-4 seconds between requests
- Configurable via command line arguments
- Random delays to avoid detection
- Separate delays for pagination and detail requests