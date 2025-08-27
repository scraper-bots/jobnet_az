"""
Database operations for JobSearch.az scraper
"""
import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from utils import (
    clean_html_content, parse_salary, parse_view_count, 
    safe_get, format_phone_number, extract_coordinates
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JobDatabase:
    def __init__(self):
        """Initialize database connection using environment variables."""
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=os.getenv('PGHOST'),
                database=os.getenv('PGDATABASE'),
                user=os.getenv('PGUSER'),
                password=os.getenv('PGPASSWORD'),
                port=os.getenv('PGPORT', 5432),
                sslmode=os.getenv('PGSSLMODE', 'require')
            )
            self.connection.autocommit = False
            
            # Set search path after connection
            with self.connection.cursor() as cursor:
                cursor.execute("SET search_path TO weapply, public")
                self.connection.commit()
            
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def execute_schema(self, schema_file_path: str):
        """Execute schema SQL file to create tables."""
        try:
            with open(schema_file_path, 'r', encoding='utf-8') as file:
                schema_sql = file.read()
            
            with self.connection.cursor() as cursor:
                cursor.execute(schema_sql)
                self.connection.commit()
                logger.info("Database schema executed successfully")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to execute schema: {e}")
            raise
    
    def job_exists(self, job_id: int) -> bool:
        """Check if a job already exists in the database."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM weapply.jobs WHERE id = %s", (job_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking if job exists: {e}")
            return False
    
    def save_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Save job data to database with all related tables.
        
        Args:
            job_data: Complete job data from API
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Check if job already exists
                if self.job_exists(job_data['id']):
                    logger.info(f"Job {job_data['id']} already exists, updating...")
                    return self.update_job(job_data)
                
                # Parse salary
                salary_amount, salary_text = parse_salary(safe_get(job_data, 'salary', default=""))
                
                # Parse view count
                view_count = parse_view_count(safe_get(job_data, 'view_count', default=0))
                
                # Clean HTML content
                raw_text = safe_get(job_data, 'text', default="")
                clean_text = clean_html_content(raw_text) if raw_text else ""
                
                # Extract coordinates
                coordinates = safe_get(job_data, 'company', 'coordinates', default={})
                lat, lng = extract_coordinates(coordinates)
                
                # Parse dates
                created_at = self._parse_date(safe_get(job_data, 'created_at'))
                deadline_at = self._parse_date(safe_get(job_data, 'deadline_at'))
                
                # Insert main job record
                job_insert_sql = """
                INSERT INTO weapply.jobs (
                    id, title, slug, is_new, is_favorite, is_vip, created_at, deadline_at,
                    salary_amount, salary_text, hide_company, view_count, phone,
                    company_id, company_title, company_slug, company_logo, company_logo_mini,
                    company_first_char, company_has_story, company_summary, company_text,
                    company_address, company_vacancy_count, company_cover,
                    category_id, category_title, category_image_mini,
                    text_content, text_content_clean, request_type, direct_apply,
                    apply_link, has_company_info, company_lat, company_lng
                ) VALUES (
                    %(id)s, %(title)s, %(slug)s, %(is_new)s, %(is_favorite)s, %(is_vip)s, 
                    %(created_at)s, %(deadline_at)s, %(salary_amount)s, %(salary_text)s, 
                    %(hide_company)s, %(view_count)s, %(phone)s, %(company_id)s, 
                    %(company_title)s, %(company_slug)s, %(company_logo)s, %(company_logo_mini)s,
                    %(company_first_char)s, %(company_has_story)s, %(company_summary)s, 
                    %(company_text)s, %(company_address)s, %(company_vacancy_count)s, 
                    %(company_cover)s, %(category_id)s, %(category_title)s, %(category_image_mini)s,
                    %(text_content)s, %(text_content_clean)s, %(request_type)s, %(direct_apply)s,
                    %(apply_link)s, %(has_company_info)s, %(company_lat)s, %(company_lng)s
                )
                """
                
                job_params = {
                    'id': job_data['id'],
                    'title': safe_get(job_data, 'title', default=""),
                    'slug': safe_get(job_data, 'slug', default=""),
                    'is_new': safe_get(job_data, 'is_new', default=False),
                    'is_favorite': safe_get(job_data, 'is_favorite', default=False),
                    'is_vip': safe_get(job_data, 'is_vip', default=False),
                    'created_at': created_at,
                    'deadline_at': deadline_at,
                    'salary_amount': salary_amount,
                    'salary_text': salary_text,
                    'hide_company': safe_get(job_data, 'hide_company', default=False),
                    'view_count': view_count,
                    'phone': format_phone_number(safe_get(job_data, 'phone', default="")),
                    'company_id': safe_get(job_data, 'company', 'id'),
                    'company_title': safe_get(job_data, 'company', 'title', default=""),
                    'company_slug': safe_get(job_data, 'company', 'slug', default=""),
                    'company_logo': safe_get(job_data, 'company', 'logo', default=""),
                    'company_logo_mini': safe_get(job_data, 'company', 'logo_mini', default=""),
                    'company_first_char': safe_get(job_data, 'company', 'first_char', default=""),
                    'company_has_story': safe_get(job_data, 'company', 'has_story', default=False),
                    'company_summary': safe_get(job_data, 'company', 'summary', default=""),
                    'company_text': clean_html_content(safe_get(job_data, 'company', 'text', default="")),
                    'company_address': safe_get(job_data, 'company', 'address', default=""),
                    'company_vacancy_count': safe_get(job_data, 'company_vacancy_count', default=0),
                    'company_cover': safe_get(job_data, 'company', 'cover', default=""),
                    'category_id': safe_get(job_data, 'category', 'id'),
                    'category_title': safe_get(job_data, 'category', 'title', default=""),
                    'category_image_mini': safe_get(job_data, 'category', 'image_mini', default=""),
                    'text_content': raw_text,
                    'text_content_clean': clean_text,
                    'request_type': safe_get(job_data, 'request_type', default=""),
                    'direct_apply': safe_get(job_data, 'direct_apply', default=False),
                    'apply_link': safe_get(job_data, 'apply_link', default=""),
                    'has_company_info': safe_get(job_data, 'has_company_info', default=False),
                    'company_lat': lat,
                    'company_lng': lng
                }
                
                cursor.execute(job_insert_sql, job_params)
                
                # Insert related data
                job_id = job_data['id']
                
                # Company phones
                phones = safe_get(job_data, 'company', 'phones', default=[])
                if phones:
                    for phone in phones:
                        clean_phone = format_phone_number(phone)
                        if clean_phone:
                            cursor.execute("""
                                INSERT INTO weapply.company_phones (job_id, phone) 
                                VALUES (%s, %s)
                            """, (job_id, clean_phone))
                
                # Company websites
                sites = safe_get(job_data, 'company', 'sites', default=[])
                if sites:
                    for site in sites:
                        if isinstance(site, dict):
                            cursor.execute("""
                                INSERT INTO weapply.company_websites (job_id, url, title) 
                                VALUES (%s, %s, %s)
                            """, (job_id, site.get('url', ''), site.get('title', '')))
                
                # Company emails
                emails = safe_get(job_data, 'company', 'email', default=[])
                if emails:
                    for email in emails:
                        if email and email.strip():
                            cursor.execute("""
                                INSERT INTO weapply.company_emails (job_id, email) 
                                VALUES (%s, %s)
                            """, (job_id, email.strip()))
                
                # Company industries
                industries = safe_get(job_data, 'company', 'industries', default=[])
                if industries:
                    for industry in industries:
                        if isinstance(industry, dict):
                            cursor.execute("""
                                INSERT INTO weapply.company_industries 
                                (job_id, industry_id, industry_title, industry_image_mini) 
                                VALUES (%s, %s, %s, %s)
                            """, (job_id, industry.get('id'), industry.get('title', ''), 
                                 industry.get('image_mini', '')))
                
                # Company gallery
                gallery = safe_get(job_data, 'company', 'gallery', default=[])
                if gallery:
                    for image_url in gallery:
                        if image_url:
                            cursor.execute("""
                                INSERT INTO weapply.company_gallery (job_id, image_url) 
                                VALUES (%s, %s)
                            """, (job_id, image_url))
                
                # Job files
                files = safe_get(job_data, 'files', default=[])
                if files:
                    for file_data in files:
                        if isinstance(file_data, dict):
                            cursor.execute("""
                                INSERT INTO weapply.job_files 
                                (job_id, file_url, file_name, file_type) 
                                VALUES (%s, %s, %s, %s)
                            """, (job_id, file_data.get('url', ''), 
                                 file_data.get('name', ''), file_data.get('type', '')))
                
                self.connection.commit()
                logger.info(f"Successfully saved job {job_id}: {job_params['title']}")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to save job {job_data.get('id', 'unknown')}: {e}")
            return False
    
    def update_job(self, job_data: Dict[str, Any]) -> bool:
        """Update existing job data."""
        try:
            with self.connection.cursor() as cursor:
                # Update main job record
                view_count = parse_view_count(safe_get(job_data, 'view_count', default=0))
                
                cursor.execute("""
                    UPDATE weapply.jobs 
                    SET view_count = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (view_count, job_data['id']))
                
                self.connection.commit()
                logger.info(f"Updated job {job_data['id']}")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to update job {job_data.get('id', 'unknown')}: {e}")
            return False
    
    def get_job_count(self) -> int:
        """Get total number of jobs in database."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM weapply.jobs")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get job count: {e}")
            return 0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Handle ISO format with timezone
            if 'T' in date_str:
                # Remove timezone part for parsing
                date_part = date_str.split('+')[0].split('-')[0:3]
                date_part = '-'.join(date_part)
                if 'T' in date_part:
                    return datetime.fromisoformat(date_str.replace('+04:00', ''))
            return None
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None