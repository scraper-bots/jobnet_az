#!/usr/bin/env python3
"""
JobNet.az Candidate Scraper
Scrapes all candidate data from JobNet API including contact information
"""

import requests
import json
import csv
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobNetScraper:
    def __init__(self):
        self.base_url = "https://api.jobnet.az/api/v1/job-seekers"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.all_candidates = []
        self.failed_candidates = []
        
    def get_candidate_listings(self, page: int = 1) -> Optional[Dict]:
        """Get candidate listings from a specific page"""
        try:
            url = f"{self.base_url}?page={page}"
            logger.info(f"Fetching page {page}: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for page {page}: {e}")
            return None
    
    def get_candidate_detail(self, slug: str) -> Optional[Dict]:
        """Get detailed candidate information by slug"""
        try:
            url = f"{self.base_url}/{slug}"
            logger.info(f"Fetching candidate detail: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching candidate {slug}: {e}")
            self.failed_candidates.append(slug)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for candidate {slug}: {e}")
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
                
                # Contact Info (this is what you specifically wanted)
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
    
    def scrape_all_candidates(self):
        """Scrape all candidates from all pages"""
        logger.info("Starting to scrape all candidates...")
        
        page = 1
        total_pages = None
        
        while True:
            # Get listings page
            listings_data = self.get_candidate_listings(page)
            
            if not listings_data:
                logger.error(f"Failed to get page {page}, stopping...")
                break
            
            # Extract pagination info
            try:
                data_section = listings_data['data'][0]['data']
                if total_pages is None:
                    total_pages = data_section['last_page']
                    logger.info(f"Total pages to scrape: {total_pages}")
                
                candidates = data_section['data']
                logger.info(f"Found {len(candidates)} candidates on page {page}")
                
                # Extract slugs and get detailed data
                for candidate in candidates:
                    slug = candidate.get('slug', '')
                    if slug:
                        logger.info(f"Processing candidate: {slug}")
                        
                        # Get detailed candidate data
                        detail_data = self.get_candidate_detail(slug)
                        
                        if detail_data:
                            # Extract relevant information
                            extracted_info = self.extract_candidate_info(detail_data)
                            if extracted_info:
                                self.all_candidates.append(extracted_info)
                                logger.info(f"Successfully processed candidate: {slug}")
                            else:
                                logger.warning(f"Failed to extract info for candidate: {slug}")
                        
                        # Rate limiting - be respectful to the API
                        time.sleep(0.5)
                
                # Check if we've reached the last page
                if page >= total_pages:
                    logger.info(f"Reached last page ({page}), stopping...")
                    break
                
                page += 1
                
                # Rate limiting between pages
                time.sleep(1)
                
            except (KeyError, IndexError) as e:
                logger.error(f"Error processing page {page} structure: {e}")
                break
        
        logger.info(f"Scraping completed! Total candidates processed: {len(self.all_candidates)}")
        if self.failed_candidates:
            logger.warning(f"Failed to process {len(self.failed_candidates)} candidates: {self.failed_candidates}")
    
    def save_to_json(self, filename: str):
        """Save all candidate data to JSON file"""
        try:
            # Create JSON-friendly version (remove CSV-specific fields)
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
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")
    
    def save_to_csv(self, filename: str):
        """Save all candidate data to CSV file"""
        try:
            if not self.all_candidates:
                logger.warning("No candidate data to save to CSV")
                return
            
            # Get CSV-friendly version (remove raw data fields)
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

def main():
    """Main function"""
    scraper = JobNetScraper()
    
    try:
        # Scrape all candidates
        scraper.scrape_all_candidates()
        
        # Generate timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"jobnet_candidates_{timestamp}.json"
        csv_filename = f"jobnet_candidates_{timestamp}.csv"
        
        # Save to files
        scraper.save_to_json(json_filename)
        scraper.save_to_csv(csv_filename)
        
        print(f"\nScraping completed successfully!")
        print(f"Total candidates processed: {len(scraper.all_candidates)}")
        print(f"JSON file: {json_filename}")
        print(f"CSV file: {csv_filename}")
        
        if scraper.failed_candidates:
            print(f"Failed candidates: {len(scraper.failed_candidates)}")
            print(f"Check scraper.log for details")
    
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\nScraping interrupted. Saving partial data...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"jobnet_candidates_partial_{timestamp}.json"
        csv_filename = f"jobnet_candidates_partial_{timestamp}.csv"
        
        scraper.save_to_json(json_filename)
        scraper.save_to_csv(csv_filename)
        
        print(f"Partial data saved:")
        print(f"Candidates processed: {len(scraper.all_candidates)}")
        print(f"JSON file: {json_filename}")
        print(f"CSV file: {csv_filename}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()