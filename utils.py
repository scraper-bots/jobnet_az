"""
Utility functions for JobSearch.az scraper
"""
import re
import html
from bs4 import BeautifulSoup
from typing import Optional, Union


def clean_html_content(html_content: str) -> str:
    """
    Clean HTML content by removing tags and converting entities to plain text.
    
    Args:
        html_content: Raw HTML content string
        
    Returns:
        Clean plain text string
    """
    if not html_content:
        return ""
    
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        
        return text.strip()
        
    except Exception as e:
        print(f"Error cleaning HTML content: {e}")
        # Fallback: simple tag removal
        return re.sub(r'<[^>]+>', '', html_content).strip()


def parse_salary(salary_value: Union[str, int, float]) -> tuple[Optional[float], str]:
    """
    Parse salary value and return numeric amount and original text.
    
    Args:
        salary_value: Salary value from API (can be string, int, or float)
        
    Returns:
        Tuple of (numeric_amount, original_text)
    """
    if not salary_value:
        return None, ""
    
    salary_text = str(salary_value).strip()
    
    if salary_text in ["", "0"]:
        return None, salary_text
    
    # Try to extract numeric value
    numeric_match = re.search(r'(\d+(?:\.\d+)?)', salary_text.replace(',', ''))
    if numeric_match:
        try:
            amount = float(numeric_match.group(1))
            return amount, salary_text
        except ValueError:
            pass
    
    return None, salary_text


def parse_view_count(view_count: Union[str, int]) -> int:
    """
    Parse view count value which can be numeric or contain 'K' suffix.
    
    Args:
        view_count: View count value from API
        
    Returns:
        Numeric view count
    """
    if not view_count:
        return 0
    
    view_str = str(view_count).strip()
    
    if view_str.endswith('K'):
        try:
            base_value = float(view_str[:-1])
            return int(base_value * 1000)
        except ValueError:
            return 0
    elif view_str.endswith('k'):
        try:
            base_value = float(view_str[:-1])
            return int(base_value * 1000)
        except ValueError:
            return 0
    
    try:
        return int(float(view_str))
    except (ValueError, TypeError):
        return 0


def safe_get(data: dict, *keys, default=None):
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search in
        *keys: Sequence of keys to traverse
        default: Default value if key path not found
        
    Returns:
        Value at key path or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def validate_job_data(job_data: dict) -> bool:
    """
    Validate that job data contains required fields.
    
    Args:
        job_data: Dictionary containing job data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['id', 'title', 'slug']
    
    for field in required_fields:
        if field not in job_data or not job_data[field]:
            return False
    
    # Validate ID is numeric
    try:
        int(job_data['id'])
    except (ValueError, TypeError):
        return False
    
    return True


def format_phone_number(phone: str) -> str:
    """
    Clean and format phone number.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Cleaned phone number
    """
    if not phone:
        return ""
    
    # Remove common formatting characters
    cleaned = re.sub(r'[^\d+\-\(\)\s]', '', phone.strip())
    
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def extract_coordinates(coordinates: dict) -> tuple[Optional[float], Optional[float]]:
    """
    Extract latitude and longitude from coordinates dict.
    
    Args:
        coordinates: Dictionary with 'lat' and 'lng' keys
        
    Returns:
        Tuple of (latitude, longitude)
    """
    if not coordinates or not isinstance(coordinates, dict):
        return None, None
    
    lat = coordinates.get('lat')
    lng = coordinates.get('lng')
    
    try:
        lat = float(lat) if lat and lat != 0 else None
        lng = float(lng) if lng and lng != 0 else None
        return lat, lng
    except (ValueError, TypeError):
        return None, None