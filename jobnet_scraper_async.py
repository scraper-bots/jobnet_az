#!/usr/bin/env python3
"""
JobNet.az Candidate Scraper - Async Optimized Version
High-performance async scraper for JobNet API using aiohttp and asyncio
"""

import asyncio
import aiohttp
import aiofiles
import json
import csv
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_async.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AsyncJobNetScraper:
    def __init__(self, max_concurrent_requests: int = 10, request_delay: float = 0.1):
        self.base_url = "https://api.jobnet.az/api/v1/job-seekers"
        self.max_concurrent_requests = max_concurrent_requests
        self.request_delay = request_delay
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        self.session = None
        self.all_candidates = []
        self.failed_candidates = []
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, url: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Make a rate-limited HTTP request with retry logic"""
        async with self.semaphore:
            max_retries = 3
            base_delay = 1
            
            for attempt in range(max_retries):
                try:
                    # Add delay for rate limiting
                    if self.request_delay > 0:
                        await asyncio.sleep(self.request_delay)
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limited
                            retry_delay = base_delay * (2 ** attempt) + (attempt * 0.5)
                            logger.warning(f"Rate limited, retrying in {retry_delay}s for URL: {url}")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"HTTP {response.status} for URL: {url}")
                            return None
                            
                except asyncio.TimeoutError:
                    retry_delay = base_delay * (2 ** attempt)
                    logger.warning(f"Timeout (attempt {attempt + 1}), retrying in {retry_delay}s for URL: {url}")
                    await asyncio.sleep(retry_delay)
                    
                except Exception as e:
                    logger.error(f"Request failed for {url}: {e}")
                    if attempt == max_retries - 1:
                        return None
                    await asyncio.sleep(base_delay * (2 ** attempt))
            
            return None
    
    async def get_candidate_listings(self, page: int) -> Optional[Dict]:
        """Get candidate listings from a specific page"""
        try:
            url = f"{self.base_url}?page={page}"
            logger.debug(f"Fetching page {page}: {url}")
            
            data = await self.make_request(url, self.session)
            if data:
                logger.info(f"Successfully fetched page {page}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            return None
    
    async def get_candidate_detail(self, slug: str) -> Optional[Dict]:
        """Get detailed candidate information by slug"""
        try:
            url = f"{self.base_url}/{slug}"
            logger.debug(f"Fetching candidate detail: {slug}")
            
            data = await self.make_request(url, self.session)
            if data:
                logger.debug(f"Successfully fetched candidate: {slug}")
                return data
            else:
                self.failed_candidates.append(slug)
                return None
                
        except Exception as e:
            logger.error(f"Error fetching candidate {slug}: {e}")
            self.failed_candidates.append(slug)
            return None
    
    def extract_candidate_info(self, candidate_data: Dict) -> Dict:
        """Extract relevant information from candidate data"""
        try:
            data = candidate_data.get('data', {})
            user = data.get('user', {})
            city = data.get('city', {})
            category = data.get('category', {})
            parent_category = category.get('parent', {})
            
            # Extract experience
            experiences = []
            for exp in data.get('jobseeker_experience', []):
                experiences.append({
                    'employer_name': exp.get('employer_name', ''),
                    'position': exp.get('position', ''),
                    'started_at': exp.get('started_at', ''),
                    'ended_at': exp.get('ended_at', ''),
                    'detailed_info': exp.get('detailed_info', ''),
                    'ongoing': exp.get('ongoing', 0)
                })
            
            # Extract skills
            skills = []
            for skill in data.get('skills', []):
                skills.append({
                    'skill_name': skill.get('skill_name', ''),
                    'knowledge_rate': skill.get('knowledge_rate', '')
                })
            
            # Extract languages
            languages = []
            for lang in data.get('jobseeker_language_skill', []):
                languages.append({
                    'name': lang.get('name', ''),
                    'rate': lang.get('rate', '')
                })
            
            # Extract education
            education = []
            for edu in data.get('education_background', []):
                education.append({
                    'university_name': edu.get('university_name', ''),
                    'speciality': edu.get('speciality', ''),
                    'started_at': edu.get('started_at', ''),
                    'ended_at': edu.get('ended_at', ''),
                    'ongoing': edu.get('ongoing', 0),
                    'education_degree_id': edu.get('education_degree_id', '')
                })
            
            # Extract certificates
            certificates = []
            for cert in data.get('certificate', []):
                certificates.append(cert)
            
            # Extract driver licenses
            licenses = []
            for license in data.get('driver_lisence', []):
                licenses.append({
                    'name': license.get('name', '')
                })
            
            # Extract working types
            working_types = []
            for wt in data.get('working_types', []):
                working_types.append({
                    'working_type_id': wt.get('working_type_id', '')
                })
            
            extracted_data = {
                # Basic Info
                'id': data.get('id', ''),
                'user_id': data.get('user_id', ''),
                'slug': data.get('slug', ''),
                'position': data.get('position', ''),
                'salary_min': data.get('salary_min', ''),
                'gender': data.get('gender', ''),
                'viewed': data.get('viewed', ''),
                'status': data.get('status', ''),
                
                # Contact Info
                'contact_email': data.get('contact_email', ''),
                'contact_phone': data.get('contact_phone', ''),
                'address': data.get('address', ''),
                'date_of_birth': data.get('date_of_birth', ''),
                
                # User Info
                'name': user.get('name', ''),
                'last_name': user.get('last_name', ''),
                'user_type': user.get('user_type', ''),
                
                # Location
                'city_id': data.get('city_id', ''),
                'city_name': city.get('name', ''),
                
                # Category
                'category_id': data.get('category_id', ''),
                'category_name': category.get('name', ''),
                'parent_category_name': parent_category.get('name', ''),
                
                # Profile
                'profile_img': data.get('profile_img', ''),
                'detailed_info': data.get('detailed_info', ''),
                
                # Dates
                'starts_at': data.get('starts_at', ''),
                'verified_at': data.get('verified_at', ''),
                'ends_at': data.get('ends_at', ''),
                
                # Premium/Sponsored status
                'isPremium': data.get('isPremium', False),
                'isSponsored': data.get('isSponsored', False),
                'premium_at': data.get('premium_at', ''),
                'premium_till': data.get('premium_till', ''),
                'sponsored_at': data.get('sponsored_at', ''),
                'sponsored_till': data.get('sponsored_till', ''),
                
                # Complex data as JSON strings for CSV
                'experiences': json.dumps(experiences, ensure_ascii=False),
                'skills': json.dumps(skills, ensure_ascii=False),
                'languages': json.dumps(languages, ensure_ascii=False),
                'education': json.dumps(education, ensure_ascii=False),
                'certificates': json.dumps(certificates, ensure_ascii=False),
                'driver_licenses': json.dumps(licenses, ensure_ascii=False),
                'working_types': json.dumps(working_types, ensure_ascii=False),
                
                # Raw data for JSON
                'raw_experiences': experiences,
                'raw_skills': skills,
                'raw_languages': languages,
                'raw_education': education,
                'raw_certificates': certificates,
                'raw_driver_licenses': licenses,
                'raw_working_types': working_types,
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting candidate info: {e}")
            return {}
    
    async def process_candidate_batch(self, candidates_batch: List[Dict]) -> List[Dict]:
        """Process a batch of candidates concurrently"""
        tasks = []
        
        for candidate in candidates_batch:
            slug = candidate.get('slug', '')
            if slug:
                task = self.get_candidate_detail(slug)
                tasks.append((slug, task))
        
        results = []
        if tasks:
            # Process all candidates in the batch concurrently
            task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (slug, _), result in zip(tasks, task_results):
                if isinstance(result, Exception):
                    logger.error(f"Exception processing candidate {slug}: {result}")
                    self.failed_candidates.append(slug)
                elif result:
                    extracted_info = self.extract_candidate_info(result)
                    if extracted_info:
                        results.append(extracted_info)
                        logger.info(f"Successfully processed candidate: {slug}")
                    else:
                        logger.warning(f"Failed to extract info for candidate: {slug}")
        
        return results
    
    async def get_all_pages_info(self) -> Tuple[int, List[List[Dict]]]:
        """Get total pages and all candidate listings from all pages"""
        logger.info("Fetching pagination info...")
        
        # Get first page to determine total pages
        first_page_data = await self.get_candidate_listings(1)
        if not first_page_data:
            raise Exception("Failed to fetch first page")
        
        try:
            data_section = first_page_data['data'][0]['data']
            total_pages = data_section['last_page']
            logger.info(f"Total pages discovered: {total_pages}")
            
            # Fetch all pages concurrently
            logger.info("Fetching all candidate listings...")
            page_tasks = [self.get_candidate_listings(page) for page in range(1, total_pages + 1)]
            page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
            
            all_candidate_batches = []
            
            for page_num, result in enumerate(page_results, 1):
                if isinstance(result, Exception):
                    logger.error(f"Exception fetching page {page_num}: {result}")
                    continue
                elif result:
                    try:
                        candidates = result['data'][0]['data']['data']
                        all_candidate_batches.append(candidates)
                        logger.info(f"Page {page_num}: Found {len(candidates)} candidates")
                    except (KeyError, IndexError, TypeError) as e:
                        logger.error(f"Error processing page {page_num} structure: {e}")
                        continue
                else:
                    logger.error(f"Failed to fetch page {page_num}")
            
            return total_pages, all_candidate_batches
            
        except (KeyError, IndexError) as e:
            raise Exception(f"Error processing pagination info: {e}")
    
    async def scrape_all_candidates(self):
        """Scrape all candidates using async/await for maximum performance"""
        start_time = time.time()
        logger.info("Starting async scraping of all candidates...")
        
        try:
            # Get all candidate listings first
            total_pages, candidate_batches = await self.get_all_pages_info()
            
            # Flatten all candidates
            all_candidates_list = []
            for batch in candidate_batches:
                all_candidates_list.extend(batch)
            
            total_candidates = len(all_candidates_list)
            logger.info(f"Total candidates to process: {total_candidates}")
            
            # Process candidates in smaller batches to control memory usage
            batch_size = 50  # Process 50 candidates at a time
            processed_count = 0
            
            for i in range(0, len(all_candidates_list), batch_size):
                batch = all_candidates_list[i:i + batch_size]
                batch_results = await self.process_candidate_batch(batch)
                
                self.all_candidates.extend(batch_results)
                processed_count += len(batch)
                
                logger.info(f"Processed batch: {processed_count}/{total_candidates} candidates "
                          f"({len(batch_results)}/{len(batch)} successful)")
                
                # Small delay between batches to be respectful
                await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error in scraping process: {e}")
            raise
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Async scraping completed in {duration:.2f} seconds!")
        logger.info(f"Total candidates processed: {len(self.all_candidates)}")
        logger.info(f"Average processing speed: {len(self.all_candidates)/duration:.2f} candidates/second")
        
        if self.failed_candidates:
            logger.warning(f"Failed to process {len(self.failed_candidates)} candidates")
    
    async def save_to_json(self, filename: str):
        """Save all candidate data to JSON file asynchronously"""
        try:
            # Create JSON-friendly version
            json_data = []
            for candidate in self.all_candidates:
                json_candidate = candidate.copy()
                # Remove string versions and keep raw data
                fields_to_remove = ['experiences', 'skills', 'languages', 'education', 'certificates', 'driver_licenses', 'working_types']
                for field in fields_to_remove:
                    json_candidate.pop(field, None)
                    
                # Rename raw fields
                raw_fields = ['raw_experiences', 'raw_skills', 'raw_languages', 'raw_education', 'raw_certificates', 'raw_driver_licenses', 'raw_working_types']
                for raw_field in raw_fields:
                    new_field = raw_field.replace('raw_', '')
                    if raw_field in json_candidate:
                        json_candidate[new_field] = json_candidate.pop(raw_field)
                
                json_data.append(json_candidate)
            
            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(json_data, ensure_ascii=False, indent=2))
            
            logger.info(f"JSON data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")
    
    def save_to_csv(self, filename: str):
        """Save all candidate data to CSV file (synchronous as CSV writing is fast)"""
        try:
            if not self.all_candidates:
                logger.warning("No candidate data to save to CSV")
                return
            
            # Get CSV-friendly version
            csv_data = []
            for candidate in self.all_candidates:
                csv_candidate = candidate.copy()
                # Remove raw fields for CSV
                raw_fields = ['raw_experiences', 'raw_skills', 'raw_languages', 'raw_education', 'raw_certificates', 'raw_driver_licenses', 'raw_working_types']
                for raw_field in raw_fields:
                    csv_candidate.pop(raw_field, None)
                csv_data.append(csv_candidate)
            
            # Get fieldnames from first candidate
            fieldnames = list(csv_data[0].keys())
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            logger.info(f"CSV data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")

async def main():
    """Main async function"""
    # Configuration
    max_concurrent = 15  # Adjust based on API limits and your connection
    request_delay = 0.05  # 50ms delay between requests
    
    async with AsyncJobNetScraper(max_concurrent, request_delay) as scraper:
        try:
            # Scrape all candidates
            await scraper.scrape_all_candidates()
            
            # Generate timestamped filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"jobnet_candidates_async_{timestamp}.json"
            csv_filename = f"jobnet_candidates_async_{timestamp}.csv"
            
            # Save to files
            await scraper.save_to_json(json_filename)
            scraper.save_to_csv(csv_filename)
            
            print(f"\n🎉 Async scraping completed successfully!")
            print(f"📊 Total candidates processed: {len(scraper.all_candidates)}")
            print(f"📄 JSON file: {json_filename}")
            print(f"📄 CSV file: {csv_filename}")
            
            if scraper.failed_candidates:
                print(f"⚠️  Failed candidates: {len(scraper.failed_candidates)}")
                print(f"📋 Check scraper_async.log for details")
        
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            print("\n⏹️  Scraping interrupted. Saving partial data...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"jobnet_candidates_async_partial_{timestamp}.json"
            csv_filename = f"jobnet_candidates_async_partial_{timestamp}.csv"
            
            await scraper.save_to_json(json_filename)
            scraper.save_to_csv(csv_filename)
            
            print(f"💾 Partial data saved:")
            print(f"📊 Candidates processed: {len(scraper.all_candidates)}")
            print(f"📄 JSON file: {json_filename}")
            print(f"📄 CSV file: {csv_filename}")
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ An error occurred: {e}")
            sys.exit(1)

def run_async_scraper():
    """Entry point that handles asyncio setup"""
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scraper stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_async_scraper()