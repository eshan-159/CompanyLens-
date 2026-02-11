"""
Crawl module for extracting short descriptions from company websites.

Uses Playwright headless browser to handle JavaScript-rendered SPAs.
Falls back to simple requests for static sites.

- Opens the company website with a real browser
- Tries to find an "About" page or similar section
- Extracts 4–5 representative lines describing what the company does

The returned string is already a short description suitable for writing
directly to the BusinessDescription column.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from config import Config
from utils import retry_with_backoff

logger = logging.getLogger("company_scraper")


class WebsiteCrawler:
    """Lightweight crawler focused on About/Company sections."""

    def __init__(self, config: Config):
        """Initialize the crawler with configuration.

        Args:
            config: Configuration object with settings
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0 Safari/537.36 CompanyScraper"
                )
            }
        )
        self._playwright = None
        self._browser = None

    def _get_browser(self):
        """Lazy-load Playwright browser."""
        if not HAS_PLAYWRIGHT:
            return None
        if self._browser is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
        return self._browser

    def _close_browser(self):
        """Close the browser when done."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def _get_soup_with_browser(self, url: str) -> Optional[BeautifulSoup]:
        """Use Playwright to get fully rendered HTML."""
        browser = self._get_browser()
        if not browser:
            return None
        try:
            page = browser.new_page()
            page.set_default_timeout(15000)
            page.goto(url, wait_until="domcontentloaded")
            # Wait for content to load
            page.wait_for_timeout(2000)
            html = page.content()
            page.close()
            return BeautifulSoup(html, "html.parser")
        except Exception as exc:
            logger.warning(f"Playwright failed for {url}: {exc}")
            return None

    def _get_soup(self, url: str, use_browser: bool = False) -> Optional[BeautifulSoup]:
        """Fetch a URL and return BeautifulSoup HTML parser if successful.
        
        Args:
            url: The URL to fetch
            use_browser: If True, use Playwright browser for JS-rendered content
        """
        # Try Playwright browser first if requested
        if use_browser:
            soup = self._get_soup_with_browser(url)
            if soup:
                return soup
        
        try:
            timeout = max(self.config.page_timeout_secs, 5)
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code != 200:
                logger.warning(f"GET {url} returned status {resp.status_code}")
                return None
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                logger.warning(f"GET {url} is not HTML (Content-Type: {content_type})")
                return None
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as exc:
            logger.warning(f"Request failed for {url}: {exc}")
            return None

    def _extract_about_paragraphs(self, soup: BeautifulSoup, max_paragraphs: int = 20) -> Optional[str]:
        """Extract ALL content from the About page for LLM processing.

        We extract as much text as possible so the LLM can create a proper summary.
        """
        paragraphs = []

        # Prefer paragraphs inside semantic containers first
        containers = soup.select("main, section, article, div[role='main']") or [soup]

        for container in containers:
            # Get paragraphs
            for p in container.find_all("p"):
                text = p.get_text(separator=" ", strip=True)
                if not text:
                    continue
                # Skip very short fragments like "Learn more"
                if len(text.split()) < 3:
                    continue
                paragraphs.append(text)
            
            # Also get headings and list items for context
            for el in container.find_all(["h1", "h2", "h3", "li"]):
                text = el.get_text(separator=" ", strip=True)
                if text and len(text.split()) >= 3:
                    paragraphs.append(text)

        if not paragraphs:
            # Try getting any text content
            text = soup.get_text(separator=" ", strip=True)
            if text:
                paragraphs = [text]

        if not paragraphs:
            return None

        # Join all content - let LLM handle summarization
        description = " ".join(paragraphs[:max_paragraphs]).strip()

        # Higher cap since LLM will summarize
        max_chars = 3000
        if len(description) > max_chars:
            description = description[:max_chars].rsplit(" ", 1)[0] + "..."

        return description or None

    def _candidate_about_urls(self, base_url: str) -> list:
        """Generate common About/Company URL patterns for a site."""
        parsed = urlparse(base_url)
        if not parsed.scheme:
            base_url = f"https://{base_url}"
            parsed = urlparse(base_url)

        base = f"{parsed.scheme}://{parsed.netloc}"
        paths = [
            "about",
            "about/",
            "about-us",
            "about-us/",
            "company",
            "company/",
            "about/company",
            "about/company/",
            "about-us/company",
            "who-we-are",
            "who-we-are/",
        ]
        return [urljoin(base, p) for p in paths]

    @retry_with_backoff(max_retries=2, base_delay=1.0)
    def crawl_website(self, url: str) -> Optional[str]:
        """Fetch About page content from the website for LLM summarization.

        Strategy (optimized for speed):
        1. Try with simple requests first (fast)
        2. Try common About URLs
        3. If no content, try homepage
        4. Only use browser as last resort for JS-heavy sites
        """
        if not url:
            return None

        logger.info(f"Crawling website: {url}")

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Phase 1: Fast requests-based crawling
        # Try About URLs first
        for about_url in self._candidate_about_urls(base)[:4]:  # Limit to 4 URLs
            soup = self._get_soup(about_url, use_browser=False)
            if not soup:
                continue
            description = self._extract_about_paragraphs(soup)
            if description and len(description) > 100:
                logger.info(f"Found About section at {about_url}")
                return description

        # Try homepage
        home_soup = self._get_soup(base, use_browser=False)
        if home_soup:
            # Look for About links
            about_links = []
            for a in home_soup.find_all("a", href=True):
                label = (a.get_text() or "").strip().lower()
                href = a["href"].lower()
                if any(k in label for k in ["about", "company", "who we are"]) or "about" in href:
                    about_links.append(urljoin(base, a["href"]))

            seen = set()
            for link in about_links[:3]:  # Limit to 3 links
                if link in seen:
                    continue
                seen.add(link)
                soup = self._get_soup(link, use_browser=False)
                if not soup:
                    continue
                description = self._extract_about_paragraphs(soup)
                if description and len(description) > 100:
                    logger.info(f"Found About via link: {link}")
                    return description

            # Use homepage content
            fallback_desc = self._extract_about_paragraphs(home_soup)
            if fallback_desc and len(fallback_desc) > 100:
                logger.info("Using homepage content")
                return fallback_desc

        # Phase 2: Browser fallback for JS sites (slower)
        if HAS_PLAYWRIGHT:
            logger.info(f"Trying browser for JS site: {base}")
            soup = self._get_soup(base, use_browser=True)
            if soup:
                description = self._extract_about_paragraphs(soup)
                if description and len(description) > 50:
                    return description

        logger.warning(f"Could not extract content from: {url}")
        return None
    
    def crawl_batch(self, urls: dict, max_workers: int = 3) -> dict:
        """
        Crawl multiple websites in parallel.
        
        Args:
            urls: Dictionary mapping company names to URLs
            max_workers: Maximum number of parallel crawls
        
        Returns:
            Dictionary mapping company names to extracted text content
        """
        results = {}
        
        def crawl_one(company: str, url: str):
            if not url:
                return company, None
            try:
                return company, self.crawl_website(url)
            except Exception as e:
                logger.error(f"Failed to crawl website for {company}: {e}")
                return company, None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(crawl_one, c, u): c for c, u in urls.items()}
            for future in as_completed(futures):
                company, content = future.result()
                results[company] = content
        
        return results
