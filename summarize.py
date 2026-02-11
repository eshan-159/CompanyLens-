"""Summarize module using Groq API.

Groq is FREE and extremely fast - 100x faster than local LLM.
Get your free API key at: https://console.groq.com/keys
"""

import logging
import os
import re
from typing import Tuple

from config import Config

logger = logging.getLogger("company_scraper")

# Try to import Groq
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    logger.warning("groq not installed. Run: pip install groq")


# Get API key from environment - GET FREE KEY AT https://console.groq.com/keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


class BusinessSummarizer:
    """Fast summarizer using Groq's free API."""

    def __init__(self, config: Config):
        self.config = config
        self._client = None

    def _get_client(self):
        """Get Groq client."""
        if not HAS_GROQ or not GROQ_API_KEY:
            return None
        
        if self._client is None:
            self._client = Groq(api_key=GROQ_API_KEY)
        return self._client

    def _quick_category(self, text: str) -> str:
        """Fast keyword-based category fallback."""
        text_lower = text.lower()
        
        categories = {
            'FinTech': ['fintech', 'payment', 'banking', 'financial', 'invest', 'lending'],
            'Cybersecurity': ['security', 'cyber', 'threat', 'penetration', 'firewall'],
            'E-commerce': ['ecommerce', 'e-commerce', 'marketplace', 'retail', 'shopping'],
            'SaaS': ['saas', 'software as a service', 'cloud platform', 'subscription'],
            'Healthcare': ['health', 'medical', 'hospital', 'patient', 'pharma'],
            'EdTech': ['education', 'learning', 'school', 'student', 'course'],
            'Logistics': ['logistics', 'shipping', 'supply chain', 'freight', 'delivery'],
            'Manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
            'AI/ML': ['artificial intelligence', 'machine learning', 'deep learning', ' ai '],
            'HR Tech': ['hr', 'human resource', 'recruitment', 'hiring', 'talent'],
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        return 'Technology'

    def _clean_text(self, text: str, max_len: int = 300) -> str:
        """Clean and truncate text."""
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > max_len:
            text = text[:max_len].rsplit(' ', 1)[0] + '...'
        return text

    def summarize_company(self, company_name: str, website_content: str) -> Tuple[str, str]:
        """Create business description using Groq API.

        Args:
            company_name: Name of the company
            website_content: Text from the About section

        Returns:
            Tuple of (business_description, category)
        """
        if not website_content or not website_content.strip():
            return ("Website content not available", "Other")

        content = re.sub(r'\s+', ' ', website_content).strip()[:1000]
        
        client = self._get_client()
        
        if not client:
            # Fallback without API
            logger.warning(f"No Groq API key, using raw content for {company_name}")
            return (self._clean_text(content), self._quick_category(content))

        try:
            logger.info(f"Groq summarizing: {company_name}")
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fast model
                messages=[
                    {
                        "role": "user",
                        "content": f"""Summarize what {company_name} does in 2-3 sentences based on this content. Include the business category.

{content}

Format:
SUMMARY: [2-3 sentences about what they do]
CATEGORY: [FinTech/SaaS/E-commerce/Healthcare/EdTech/Logistics/Cybersecurity/Manufacturing/AI/Other]"""
                    }
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            output = response.choices[0].message.content.strip()
            
            # Parse response
            description = self._clean_text(content)
            category = self._quick_category(content)
            
            if "SUMMARY:" in output:
                parts = output.split("CATEGORY:")
                desc = parts[0].replace("SUMMARY:", "").strip()
                if desc:
                    description = desc
                
                if len(parts) > 1:
                    cat = parts[1].strip().split()[0].strip()
                    if cat:
                        category = cat

            logger.info(f"Done: {company_name} -> {category}")
            return (description, category)

        except Exception as e:
            logger.error(f"Groq error for {company_name}: {e}")
            return (self._clean_text(content), self._quick_category(content))

    def summarize_batch(self, companies_content: dict) -> dict:
        """Summarize multiple companies."""
        results = {}
        
        for company, content in companies_content.items():
            description, category = self.summarize_company(company, content or "")
            results[company] = (description, category)
        
        return results
