"""
Configuration management for the company scraper pipeline.
All settings are configurable via environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration settings for the pipeline."""
    
    # API Keys (required)
    apify_api_token: str
    llm_api_key: str
    
    # LLM Settings
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    
    # Batch Processing
    batch_size: int = 30
    max_retries: int = 3
    retry_delay: float = 2.0
    
    # Crawl Settings
    crawl_depth: int = 1
    max_pages_per_domain: int = 1
    page_timeout_secs: int = 20
    
    # Search Settings
    search_results_limit: int = 5
    
    # Rate Limiting
    request_delay: float = 1.0  # seconds between requests
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        apify_token = os.getenv("APIFY_API_TOKEN")
        llm_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not apify_token:
            raise ValueError("APIFY_API_TOKEN environment variable is required")
        if not llm_key:
            raise ValueError("LLM_API_KEY or OPENAI_API_KEY environment variable is required")
        
        return cls(
            apify_api_token=apify_token,
            llm_api_key=llm_key,
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            batch_size=int(os.getenv("BATCH_SIZE", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "2.0")),
            crawl_depth=int(os.getenv("CRAWL_DEPTH", "2")),
            max_pages_per_domain=int(os.getenv("MAX_PAGES_PER_DOMAIN", "3")),
            page_timeout_secs=int(os.getenv("PAGE_TIMEOUT_SECS", "30")),
            search_results_limit=int(os.getenv("SEARCH_RESULTS_LIMIT", "5")),
            request_delay=float(os.getenv("REQUEST_DELAY", "1.0")),
        )


# Industry categories for classification
INDUSTRY_CATEGORIES = [
    "ITES",
    "BPO", 
    "IT Services",
    "SaaS",
    "FinTech",
    "Manufacturing",
    "Healthcare",
    "E-commerce",
    "Consulting",
    "Other"
]

# Domains to exclude from search results (not official company websites)
EXCLUDED_DOMAINS = [
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "youtube.com",
    "wikipedia.org",
    "crunchbase.com",
    "glassdoor.com",
    "indeed.com",
    "bloomberg.com",
    "reuters.com",
    "forbes.com",
    "techcrunch.com",
    "news.google.com",
    "yelp.com",
    "bbb.org",
    "zoominfo.com",
    "dnb.com",
    "hoovers.com",
    "owler.com",
    "pitchbook.com",
    "apollo.io",
    "g2.com",
    "capterra.com",
    "trustpilot.com",
]
