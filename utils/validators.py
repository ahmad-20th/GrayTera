import re
from urllib.parse import urlparse


def is_valid_domain(domain: str) -> bool:
    """Validate if string is a valid domain name"""
    if not isinstance(domain, str) or not domain:
        return False
    
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain.lower()))


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent injection"""
    # Remove potentially dangerous characters
    return re.sub(r'[^\w\s\-\.]', '', user_input)
