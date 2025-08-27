#!/usr/bin/env python3
"""
Check database contents
"""
import os
from dotenv import load_dotenv
from database import JobDatabase

# Load environment variables
load_dotenv()

def check_database():
    db = JobDatabase()
    
    try:
        with db.connection.cursor() as cursor:
            # Total jobs
            cursor.execute('SELECT COUNT(*) FROM weapply.jobs')
            job_count = cursor.fetchone()[0]
            print(f'Total jobs: {job_count}')
            
            if job_count > 0:
                # Sample jobs
                cursor.execute('''
                    SELECT id, title, company_title, salary_amount, view_count 
                    FROM weapply.jobs 
                    ORDER BY id 
                    LIMIT 5
                ''')
                jobs = cursor.fetchall()
                print('\nSample jobs:')
                for job in jobs:
                    title = job[1][:60] + '...' if len(job[1]) > 60 else job[1]
                    print(f'ID: {job[0]}, Title: {title}')
                    print(f'    Company: {job[2]}, Salary: {job[3]}, Views: {job[4]}')
                    print()
                
                # Related data counts
                cursor.execute('SELECT COUNT(*) FROM weapply.company_phones')
                phone_count = cursor.fetchone()[0]
                print(f'Company phones: {phone_count}')
                
                cursor.execute('SELECT COUNT(*) FROM weapply.company_emails')
                email_count = cursor.fetchone()[0]
                print(f'Company emails: {email_count}')
                
                cursor.execute('SELECT COUNT(*) FROM weapply.company_websites')
                website_count = cursor.fetchone()[0]
                print(f'Company websites: {website_count}')
                
                cursor.execute('SELECT COUNT(*) FROM weapply.company_industries')
                industry_count = cursor.fetchone()[0]
                print(f'Company industries: {industry_count}')
                
                # Check for HTML content cleaning
                cursor.execute('''
                    SELECT id, title, LENGTH(text_content) as orig_len, 
                           LENGTH(text_content_clean) as clean_len
                    FROM weapply.jobs 
                    WHERE text_content IS NOT NULL AND text_content != ''
                    LIMIT 3
                ''')
                content_samples = cursor.fetchall()
                print(f'\nContent cleaning samples:')
                for sample in content_samples:
                    print(f'Job {sample[0]}: Original {sample[2]} chars -> Clean {sample[3]} chars')
            
    finally:
        db.close()

if __name__ == '__main__':
    check_database()