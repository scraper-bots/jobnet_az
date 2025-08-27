#!/usr/bin/env python3
"""
Example script to run a full scrape of JobSearch.az
This will scrape all available jobs and save them to the database.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("=== JobSearch.az Full Scraper ===")
    print("This will scrape ALL jobs from JobSearch.az and save them to PostgreSQL")
    print("This may take several hours depending on the number of jobs available.")
    print()
    
    # Confirm database connection
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        sys.exit(1)
    
    print(f"Database: {os.getenv('PGDATABASE')} at {os.getenv('PGHOST')}")
    
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    # Import here to check dependencies
    try:
        from main import scrape_and_save_jobs
    except ImportError as e:
        print(f"ERROR: Missing dependencies: {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\nStarting full scrape...")
    print("Logs will be saved to a timestamped file.")
    print("You can stop the scraper at any time with Ctrl+C")
    print()
    
    try:
        # Run full scrape with conservative delays
        scrape_and_save_jobs(
            max_pages=None,  # All pages
            delay_range=(3, 6)  # Slower to be respectful
        )
        print("\n=== SCRAPING COMPLETED SUCCESSFULLY ===")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        print("Partial data has been saved to the database.")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()