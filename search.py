"""
Fast search module - uses DuckDuckGo instead of slow Apify.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import quote_plus, urlparse

import requests

from config import Config

logger = logging.getLogger("company_scraper")


class CompanySearcher:
    """Fast company website search using DuckDuckGo HTML."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def find_company_website(self, company_name: str) -> Optional[str]:
        """Search for company website using DuckDuckGo."""
        logger.info(f"Searching for: {company_name}")
        
        try:
            query = quote_plus(f"{company_name} official website")
            url = f"https://html.duckduckgo.com/html/?q={query}"
            
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                return None
            
            # Extract URLs from results
            # DuckDuckGo HTML wraps URLs in uddg= parameter
            matches = re.findall(r'uddg=([^&"]+)', resp.text)
            
            for match in matches[:5]:
                try:
                    from urllib.parse import unquote
                    decoded_url = unquote(match)
                    
                    # Skip non-company URLs
                    if self._is_valid_company_url(decoded_url, company_name):
                        logger.info(f"Found website for {company_name}: {decoded_url}")
                        return decoded_url
                except:
                    continue
            
            # Fallback: try to find any URL in the page
            all_urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
            for u in all_urls[:10]:
                if self._is_valid_company_url(u, company_name):
                    logger.info(f"Found website for {company_name}: {u}")
                    return u
            
            logger.warning(f"No website found for: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Search failed for {company_name}: {e}")
            return None

    def _is_valid_company_url(self, url: str, company_name: str) -> bool:
        """Check if URL looks like a company website."""
        if not url or not url.startswith('http'):
            return False
        
        # Skip known non-company sites
        skip_domains = [
            'wikipedia.org', 'linkedin.com', 'facebook.com', 'twitter.com',
            'youtube.com', 'instagram.com', 'crunchbase.com', 'bloomberg.com',
            'reuters.com', 'forbes.com', 'google.com', 'duckduckgo.com',
            'amazon.com', 'yelp.com', 'glassdoor.com', 'indeed.com',
            'zaubacorp.com', 'tofler.in', 'ambitionbox.com'
        ]
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for skip in skip_domains:
            if skip in domain:
                return False
        
        return True

    def search_batch(self, companies: list, max_workers: int = 5) -> dict:
        """Search for multiple companies in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.find_company_website, c): c 
                for c in companies
            }
            
            for future in as_completed(futures):
                company = futures[future]
                try:
                    results[company] = future.result()
                except Exception as e:
                    logger.error(f"Search error for {company}: {e}")
                    results[company] = None
        
        return results
