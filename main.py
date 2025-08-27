#!/usr/bin/env python3
"""
Main script for JobSearch.az scraper
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

from scraper import JobSearchScraper
from database import JobDatabase
from utils import validate_job_data

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def setup_database(db: JobDatabase):
    """Set up database schema."""
    try:
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            db.execute_schema(schema_path)
            logger.info("Database schema setup completed")
        else:
            logger.warning("Schema file not found, assuming database is already set up")
    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        raise


def scrape_and_save_jobs(max_pages=None, delay_range=(2, 4)):
    """Main function to scrape jobs and save to database."""
    
    # Initialize components
    scraper = JobSearchScraper()
    db = JobDatabase()
    
    try:
        # Setup database
        setup_database(db)
        
        # Get initial job count
        initial_count = db.get_job_count()
        logger.info(f"Starting scraper. Current database has {initial_count} jobs")
        
        # Scrape all jobs
        logger.info(f"Starting to scrape jobs (max_pages: {max_pages})")
        jobs = scraper.scrape_all_jobs(max_pages=max_pages, delay_range=delay_range)
        
        if not jobs:
            logger.warning("No jobs scraped")
            return
        
        logger.info(f"Scraped {len(jobs)} jobs, now saving to database...")
        
        # Save jobs to database
        saved_count = 0
        failed_count = 0
        
        for i, job in enumerate(jobs, 1):
            try:
                if not validate_job_data(job):
                    logger.warning(f"Job {i}/{len(jobs)}: Invalid data, skipping")
                    failed_count += 1
                    continue
                
                if db.save_job(job):
                    saved_count += 1
                    if saved_count % 10 == 0:
                        logger.info(f"Progress: {saved_count}/{len(jobs)} jobs saved")
                else:
                    failed_count += 1
                    logger.warning(f"Job {i}/{len(jobs)}: Failed to save job {job.get('id', 'unknown')}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Job {i}/{len(jobs)}: Error processing job {job.get('id', 'unknown')}: {e}")
        
        # Final statistics
        final_count = db.get_job_count()
        new_jobs = final_count - initial_count
        
        logger.info("=== SCRAPING COMPLETED ===")
        logger.info(f"Jobs scraped: {len(jobs)}")
        logger.info(f"Jobs saved successfully: {saved_count}")
        logger.info(f"Jobs failed to save: {failed_count}")
        logger.info(f"Database jobs before: {initial_count}")
        logger.info(f"Database jobs after: {final_count}")
        logger.info(f"New jobs added: {new_jobs}")
        
    except Exception as e:
        logger.error(f"Critical error in scraping process: {e}")
        raise
    finally:
        db.close()
        logger.info("Database connection closed")


def scrape_specific_jobs(job_slugs, delay_range=(2, 4)):
    """Scrape specific jobs by slugs."""
    
    scraper = JobSearchScraper()
    db = JobDatabase()
    
    try:
        # Setup database
        setup_database(db)
        
        logger.info(f"Scraping {len(job_slugs)} specific jobs")
        jobs = scraper.scrape_specific_jobs(job_slugs, delay_range=delay_range)
        
        if not jobs:
            logger.warning("No jobs scraped")
            return
        
        logger.info(f"Scraped {len(jobs)} jobs, now saving to database...")
        
        # Save jobs to database
        saved_count = 0
        failed_count = 0
        
        for job in jobs:
            try:
                if not validate_job_data(job):
                    logger.warning(f"Invalid data for job {job.get('id', 'unknown')}, skipping")
                    failed_count += 1
                    continue
                
                if db.save_job(job):
                    saved_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing job {job.get('id', 'unknown')}: {e}")
        
        logger.info(f"Completed: {saved_count} saved, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Critical error in scraping process: {e}")
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='JobSearch.az Scraper')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to scrape')
    parser.add_argument('--delay-min', type=float, default=2, help='Minimum delay between requests (seconds)')
    parser.add_argument('--delay-max', type=float, default=4, help='Maximum delay between requests (seconds)')
    parser.add_argument('--slugs', nargs='+', help='Specific job slugs to scrape')
    parser.add_argument('--setup-only', action='store_true', help='Only setup database schema')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only first page')
    
    args = parser.parse_args()
    
    # Validate environment variables
    required_env_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    try:
        if args.setup_only:
            # Setup database only
            db = JobDatabase()
            setup_database(db)
            db.close()
            logger.info("Database setup completed")
            return
        
        delay_range = (args.delay_min, args.delay_max)
        
        if args.test:
            logger.info("Running in test mode (first page only)")
            scrape_and_save_jobs(max_pages=1, delay_range=delay_range)
        elif args.slugs:
            # Scrape specific jobs
            scrape_specific_jobs(args.slugs, delay_range=delay_range)
        else:
            # Scrape all jobs
            scrape_and_save_jobs(max_pages=args.max_pages, delay_range=delay_range)
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()