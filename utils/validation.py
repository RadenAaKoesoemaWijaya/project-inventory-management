import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """Validate phone number format (Indonesian)"""
    if not phone:
        return False
    # Allow +62, 62, or 0 prefix, followed by 9-13 digits
    pattern = r'^(\+62|62|0)[0-9]{9,13}$'
    return bool(re.match(pattern, phone))

def validate_coordinates(lat, lng):
    """Validate latitude and longitude"""
    try:
        lat = float(lat)
        lng = float(lng)
        if not (-90 <= lat <= 90):
            return False
        if not (-180 <= lng <= 180):
            return False
        return True
    except (ValueError, TypeError):
        return False

def validate_positive_number(value, allow_zero=False):
    """Validate positive number"""
    try:
        val = float(value)
        if allow_zero:
            return val >= 0
        return val > 0
    except (ValueError, TypeError):
        return False

def validate_date(date_str, format='%Y-%m-%d'):
    """Validate date string format"""
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def sanitize_input(text):
    """Sanitize text input to prevent injection (basic)"""
    if not isinstance(text, str):
        return text
    # Remove potential dangerous characters for SQL/HTML
    return text.replace("'", "''").strip()
