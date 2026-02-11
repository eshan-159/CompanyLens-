"""
Utility functions for the company scraper pipeline.
"""

import logging
import time
from functools import wraps
from typing import Callable, Any, Optional
from urllib.parse import urlparse

from config import EXCLUDED_DOMAINS


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger("company_scraper")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (doubles each attempt)
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logging.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator


def is_valid_company_url(url: str) -> bool:
    """
    Validate if a URL appears to be an official company website.
    
    Excludes:
    - Social media platforms
    - News sites
    - Business directories
    - Job boards
    
    Args:
        url: URL to validate
    
    Returns:
        True if URL appears to be an official company website
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc
        
        # Remove www. prefix for comparison
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Check against excluded domains
        for excluded in EXCLUDED_DOMAINS:
            if excluded in domain:
                return False
        
        # Basic validation
        if not domain or "." not in domain:
            return False
        
        return True
    except Exception:
        return False


def extract_domain(url: str) -> Optional[str]:
    """
    Extract the base domain from a URL.
    
    Args:
        url: Full URL
    
    Returns:
        Base domain or None if invalid
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return None


def clean_text(text: str, max_length: int = 15000) -> str:
    """
    Clean and truncate scraped text for LLM processing.
    
    Args:
        text: Raw scraped text
        max_length: Maximum character length
    
    Returns:
        Cleaned and truncated text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    cleaned = "\n".join(cleaned_lines)
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "\n...[truncated]"
    
    return cleaned


def validate_csv_schema(df, required_columns: list) -> bool:
    """
    Validate that a DataFrame has required columns.
    
    Args:
        df: pandas DataFrame
        required_columns: List of required column names
    
    Returns:
        True if all required columns exist
    
    Raises:
        ValueError: If required columns are missing
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")
    return True


def batch_items(items: list, batch_size: int) -> list:
    """
    Split a list into batches.
    
    Args:
        items: List of items
        batch_size: Size of each batch
    
    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
