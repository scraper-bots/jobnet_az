"""
JobSearch.az API scraper
"""
import requests
import time
import logging
import random
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from utils import validate_job_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JobSearchScraper:
    def __init__(self):
        """Initialize the scraper with headers and session."""
        self.session = requests.Session()
        self.base_url = "https://www.jobsearch.az"
        self.api_base = "https://www.jobsearch.az/api-az"
        
        # Headers based on the provided example - CRITICAL FOR API ACCESS
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://www.jobsearch.az/vacancies',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        self.session.headers.update(self.headers)
        
        # Initialize session with first request to get cookies
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by making a request to get necessary cookies."""
        try:
            # Make initial request to get session cookies
            response = self.session.get(f"{self.base_url}/vacancies")
            if response.status_code == 200:
                logger.info("Session initialized successfully")
            else:
                logger.warning(f"Session initialization returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
    
    def fetch_jobs_page(self, page: int = 1, ignore_param: str = "", ignore_hash: str = "") -> Dict[str, Any]:
        """
        Fetch jobs from a specific page.
        
        Args:
            page: Page number to fetch
            ignore_param: Ignore parameter from pagination
            ignore_hash: Ignore hash from pagination
            
        Returns:
            API response data
        """
        try:
            url = f"{self.api_base}/vacancies-az"
            params = {
                'hl': 'az',
                'page': page
            }
            
            # Add ignore parameters if provided (from pagination)
            if ignore_param:
                params['ignore'] = ignore_param
            if ignore_hash:
                params['ignore_hash'] = ignore_hash
            
            logger.info(f"Fetching jobs page {page}...")
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched page {page} with {len(data.get('items', []))} jobs")
                return data
            else:
                logger.error(f"Failed to fetch page {page}: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching jobs page {page}: {e}")
            return {}
    
    def fetch_job_details(self, slug: str) -> Dict[str, Any]:
        """
        Fetch detailed job information using the job slug.
        
        Args:
            slug: Job slug from the jobs list
            
        Returns:
            Detailed job data
        """
        try:
            url = f"{self.api_base}/vacancies-az/{slug}"
            params = {'hl': 'az'}
            
            # Update referer for detail page
            detail_headers = self.headers.copy()
            detail_headers['referer'] = f"{self.base_url}/vacancies/{slug}"
            
            logger.debug(f"Fetching job details for slug: {slug}")
            
            response = self.session.get(url, params=params, headers=detail_headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Successfully fetched details for job {data.get('id', 'unknown')}")
                return data
            else:
                logger.error(f"Failed to fetch job details for {slug}: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching job details for {slug}: {e}")
            return {}
    
    def parse_pagination_params(self, next_url: str) -> tuple[str, str]:
        """
        Parse ignore parameters from the next page URL.
        
        Args:
            next_url: URL of the next page
            
        Returns:
            Tuple of (ignore_param, ignore_hash)
        """
        try:
            if not next_url:
                return "", ""
            
            parsed = urlparse(next_url)
            params = parse_qs(parsed.query)
            
            ignore_param = params.get('ignore', [''])[0]
            ignore_hash = params.get('ignore_hash', [''])[0]
            
            return ignore_param, ignore_hash
            
        except Exception as e:
            logger.error(f"Error parsing pagination params from {next_url}: {e}")
            return "", ""
    
    def scrape_all_jobs(self, max_pages: Optional[int] = None, delay_range: tuple = (1, 3)) -> List[Dict[str, Any]]:
        """
        Scrape all jobs with pagination support.
        
        Args:
            max_pages: Maximum number of pages to scrape (None for all)
            delay_range: Range of seconds to wait between requests
            
        Returns:
            List of all job data
        """
        all_jobs = []
        page = 1
        ignore_param = ""
        ignore_hash = ""
        
        logger.info("Starting to scrape all jobs...")
        
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached maximum pages limit: {max_pages}")
                break
            
            # Fetch jobs page
            page_data = self.fetch_jobs_page(page, ignore_param, ignore_hash)
            
            if not page_data or 'items' not in page_data:
                logger.warning(f"No data found for page {page}, stopping...")
                break
            
            jobs = page_data['items']
            
            if not jobs:
                logger.info(f"No jobs found on page {page}, stopping...")
                break
            
            logger.info(f"Processing {len(jobs)} jobs from page {page}")
            
            # Fetch detailed data for each job
            for i, job in enumerate(jobs):
                if not validate_job_data(job):
                    logger.warning(f"Invalid job data for job {job.get('id', 'unknown')}")
                    continue
                
                # Add some delay between detail requests
                if i > 0:
                    delay = random.uniform(delay_range[0], delay_range[1])
                    time.sleep(delay)
                
                # Fetch detailed job information
                detailed_job = self.fetch_job_details(job['slug'])
                
                if detailed_job:
                    # Merge basic info with detailed info
                    detailed_job['view_count'] = job.get('view_count', 0)  # Keep original view count
                    all_jobs.append(detailed_job)
                    logger.info(f"Added job {detailed_job['id']}: {detailed_job['title']}")
                else:
                    logger.warning(f"Failed to fetch details for job {job.get('id', 'unknown')}")
            
            # Check for next page
            next_url = page_data.get('next')
            if not next_url:
                logger.info("No more pages available")
                break
            
            # Parse pagination parameters for next request
            ignore_param, ignore_hash = self.parse_pagination_params(next_url)
            
            page += 1
            
            # Add delay between pages
            delay = random.uniform(delay_range[0], delay_range[1])
            logger.info(f"Waiting {delay:.1f} seconds before next page...")
            time.sleep(delay)
        
        logger.info(f"Scraped {len(all_jobs)} jobs total from {page-1} pages")
        return all_jobs
    
    def scrape_specific_jobs(self, job_slugs: List[str], delay_range: tuple = (1, 3)) -> List[Dict[str, Any]]:
        """
        Scrape specific jobs by their slugs.
        
        Args:
            job_slugs: List of job slugs to scrape
            delay_range: Range of seconds to wait between requests
            
        Returns:
            List of job data
        """
        jobs = []
        
        logger.info(f"Scraping {len(job_slugs)} specific jobs...")
        
        for i, slug in enumerate(job_slugs):
            if i > 0:
                delay = random.uniform(delay_range[0], delay_range[1])
                time.sleep(delay)
            
            job_data = self.fetch_job_details(slug)
            if job_data:
                jobs.append(job_data)
                logger.info(f"Scraped job {job_data['id']}: {job_data['title']}")
            else:
                logger.warning(f"Failed to scrape job with slug: {slug}")
        
        logger.info(f"Successfully scraped {len(jobs)} out of {len(job_slugs)} requested jobs")
        return jobs