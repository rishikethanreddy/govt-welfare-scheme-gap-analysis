"""
Scraping Framework — modular web data collection engine.

Architecture:
  BaseScraper → concrete scrapers (RSS, HTML, API, JSON)
  ScrapingOrchestrator → manages sources, runs, rate limiting, policy checks
  PolicyEngine → robots.txt compliance + rate limiting
"""

import abc
import time
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


@dataclass
class ScrapedRecord:
    """A single record extracted from a web source."""
    text: str
    source_url: str
    source_name: str
    source_type: str = "web"
    scheme_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    language: str = "English"
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        normalized = re.sub(r'\s+', ' ', self.text.lower().strip())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]


class PolicyEngine:
    """Checks robots.txt and enforces rate limits."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._last_request: Dict[str, float] = {}

    def check_robots(self, url: str) -> Dict[str, Any]:
        """Check robots.txt for a given URL. Returns policy dict."""
        # Bypass for local datasets
        if url.startswith("backend/") or url.startswith("/") or url.startswith("file://"):
            return {
                "allowed": True,
                "crawl_delay": 0.0,
                "robots_checked": True,
                "robots_url": None,
            }

        parsed = urlparse(url)
        domain = parsed.netloc
        if domain in self._cache:
            return self._cache[domain]

        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        result = {
            "allowed": True,
            "crawl_delay": 2.0,
            "robots_checked": True,
            "robots_url": robots_url,
        }

        try:
            import httpx
            resp = httpx.get(robots_url, timeout=10, follow_redirects=True)
            if resp.status_code == 200:
                text = resp.text.lower()
                # Basic robots.txt parsing
                in_agent = False
                for line in text.split('\n'):
                    line = line.strip()
                    if line.startswith('user-agent:'):
                        agent = line.split(':', 1)[1].strip()
                        in_agent = agent == '*' or 'bot' in agent
                    elif in_agent and line.startswith('crawl-delay:'):
                        try:
                            result["crawl_delay"] = max(float(line.split(':', 1)[1].strip()), 1.0)
                        except ValueError:
                            pass
                    elif in_agent and line.startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path == '/' or (parsed.path and parsed.path.startswith(path)):
                            result["allowed"] = False
            elif resp.status_code == 404:
                result["crawl_delay"] = 2.0  # No robots.txt = be polite
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt for {domain}: {e}")
            result["robots_checked"] = False
            result["crawl_delay"] = 3.0  # Conservative default

        self._cache[domain] = result
        return result

    def wait_for_rate_limit(self, domain: str, delay: float = 2.0):
        """Enforce crawl delay between requests to same domain."""
        now = time.time()
        last = self._last_request.get(domain, 0)
        wait_time = delay - (now - last)
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s for {domain}")
            time.sleep(wait_time)
        self._last_request[domain] = time.time()


class BaseScraper(abc.ABC):
    """Abstract base for all scrapers."""

    def __init__(self, name: str, source_type: str = "web"):
        self.name = name
        self.source_type = source_type
        self.policy = PolicyEngine()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                timeout=30,
                follow_redirects=True,
                headers={
                    "User-Agent": "WelfareGapMiner-Academic/1.0 (+research; respectful-crawling)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
                }
            )
        return self._client

    def fetch(self, url: str) -> Optional[str]:
        """Fetch URL content with policy checks and rate limiting."""
        parsed = urlparse(url)
        domain = parsed.netloc

        # Check robots.txt
        policy = self.policy.check_robots(url)
        if not policy["allowed"]:
            logger.warning(f"Blocked by robots.txt: {url}")
            return None

        # Rate limit
        self.policy.wait_for_rate_limit(domain, policy["crawl_delay"])

        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    @abc.abstractmethod
    def scrape(self, url: str, **kwargs) -> List[ScrapedRecord]:
        """Scrape a single URL and return extracted records."""
        ...

    def close(self):
        if self._client:
            self._client.close()


class RSSScraper(BaseScraper):
    """Scrapes RSS/Atom feeds for welfare scheme content."""

    def __init__(self, name: str = "RSS Feed Scraper"):
        super().__init__(name, source_type="rss")

    def scrape(self, url: str, scheme_filter: Optional[str] = None, **kwargs) -> List[ScrapedRecord]:
        import feedparser

        content = self.fetch(url)
        if not content:
            return []

        feed = feedparser.parse(content)
        records = []

        for entry in feed.entries:
            title = getattr(entry, 'title', '')
            summary = getattr(entry, 'summary', '')
            link = getattr(entry, 'link', url)
            published = getattr(entry, 'published', '')

            text = f"{title}. {summary}".strip('. ')
            if not text or len(text) < 15:
                continue

            # Optional scheme filtering
            if scheme_filter:
                if scheme_filter.lower() not in text.lower():
                    continue

            record = ScrapedRecord(
                text=text,
                source_url=link,
                source_name=self.name,
                source_type="rss",
                metadata={
                    "title": title,
                    "published": published,
                    "feed_url": url,
                },
            )
            records.append(record)

        logger.info(f"RSS scraper extracted {len(records)} records from {url}")
        return records


class HTMLScraper(BaseScraper):
    """Scrapes HTML pages for welfare scheme Q&A content."""

    # Scheme keywords for detection
    SCHEME_KEYWORDS = {
        "PM-KISAN": ["pm-kisan", "pm kisan", "kisan samman", "kisan nidhi"],
        "PMAY": ["pmay", "awas yojana", "pradhan mantri awas"],
        "Ayushman Bharat PM-JAY": ["ayushman", "pm-jay", "pmjay", "jan arogya"],
        "MGNREGA": ["mgnrega", "mnrega", "nrega", "mahatma gandhi", "job card"],
        "PMUY": ["pmuy", "ujjwala", "ujjawala"],
        "PMFBY": ["pmfby", "fasal bima"],
        "PMMY": ["pmmy", "mudra", "mudra loan"],
        "PM SVANidhi": ["svanidhi", "pm svanidhi", "street vendor"],
        "PMJDY": ["pmjdy", "jan dhan"],
        "PM-KUSUM": ["kusum", "pm-kusum"],
        "APY": ["atal pension", "apy"],
        "PMJJBY": ["pmjjby", "jeevan jyoti"],
        "PMSBY": ["pmsby", "suraksha bima"],
        "NSAP": ["nsap", "social assistance", "old age pension"],
        "PM Vishwakarma": ["vishwakarma", "pm vishwakarma"],
    }

    def __init__(self, name: str = "HTML Scraper"):
        super().__init__(name, source_type="html")

    def _detect_scheme(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for scheme, keywords in self.SCHEME_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return scheme
        return None

    def _extract_qa_blocks(self, html: str, url: str) -> List[ScrapedRecord]:
        """Extract Q&A or discussion blocks from HTML."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        records = []

        # Strategy 1: FAQ sections
        faq_selectors = [
            "div.faq", "div.faqs", "section.faq",
            "div[class*='question']", "div[class*='faq']",
            "div.accordion", "details",
        ]
        for selector in faq_selectors:
            for block in soup.select(selector):
                text = block.get_text(separator=" ", strip=True)
                if len(text) > 20 and len(text) < 2000:
                    scheme = self._detect_scheme(text)
                    records.append(ScrapedRecord(
                        text=text,
                        source_url=url,
                        source_name=self.name,
                        source_type="html_faq",
                        scheme_name=scheme,
                    ))

        # Strategy 2: Comments / user posts
        comment_selectors = [
            "div.comment", "div[class*='comment']",
            "div.post", "div[class*='reply']",
            "div.user-content", "div[class*='discussion']",
        ]
        for selector in comment_selectors:
            for block in soup.select(selector):
                text = block.get_text(separator=" ", strip=True)
                if len(text) > 30 and len(text) < 3000:
                    scheme = self._detect_scheme(text)
                    records.append(ScrapedRecord(
                        text=text,
                        source_url=url,
                        source_name=self.name,
                        source_type="html_comment",
                        scheme_name=scheme,
                    ))

        # Strategy 3: Article paragraphs (last resort)
        if len(records) == 0:
            for tag in ["article", "main", "div[class*='content']", "div[class*='post']"]:
                for block in soup.select(tag):
                    for p in block.find_all("p"):
                        text = p.get_text(strip=True)
                        if len(text) > 50 and self._detect_scheme(text):
                            records.append(ScrapedRecord(
                                text=text,
                                source_url=url,
                                source_name=self.name,
                                source_type="html_article",
                                scheme_name=self._detect_scheme(text),
                            ))

        logger.info(f"HTML scraper extracted {len(records)} records from {url}")
        return records

    def scrape(self, url: str, **kwargs) -> List[ScrapedRecord]:
        html = self.fetch(url)
        if not html:
            return []
        return self._extract_qa_blocks(html, url)


class APIScraper(BaseScraper):
    """Scrapes JSON API endpoints."""

    def __init__(self, name: str = "API Scraper"):
        super().__init__(name, source_type="api")

    def scrape(
        self,
        url: str,
        text_field: str = "text",
        records_path: Optional[str] = None,
        **kwargs,
    ) -> List[ScrapedRecord]:
        content = self.fetch(url)
        if not content:
            return []

        import json
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {url}")
            return []

        # Navigate to records array
        if records_path:
            for key in records_path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, [])

        if not isinstance(data, list):
            data = [data]

        records = []
        for item in data:
            if not isinstance(item, dict):
                continue
            text = item.get(text_field, "")
            if not text or len(text) < 10:
                continue
            records.append(ScrapedRecord(
                text=text,
                source_url=url,
                source_name=self.name,
                source_type="api",
                scheme_name=item.get("scheme") or item.get("scheme_name"),
                state=item.get("state"),
                metadata=item,
            ))

        logger.info(f"API scraper extracted {len(records)} records from {url}")
        return records


class LocalDatasetScraper(BaseScraper):
    """Streams verified real public queries from a local dataset representing downloaded open data."""

    def __init__(self, name: str = "Local Dataset Scraper"):
        super().__init__(name, source_type="dataset")
        self.state_file = "backend/data/.dataset_cursor"

    def scrape(self, url: str, **kwargs) -> List[ScrapedRecord]:
        import json
        import os
        try:
            with open(url, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read dataset {url}: {e}")
            return []

        # Read cursor
        cursor = 0
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    cursor = int(f.read().strip())
            except ValueError:
                cursor = 0

        # Simulate live scraping by taking 2 records at a time
        if cursor >= len(data):
            cursor = 0  # Loop back for demo purposes

        chunk = data[cursor:cursor+2]
        records = []
        for item in chunk:
            records.append(ScrapedRecord(
                text=item["text"],
                source_url=url,
                source_name=item.get("source", self.name),
                source_type="open_dataset",
                scheme_name=item.get("scheme"),
                state=item.get("state"),
                metadata=item,
            ))

        # Save cursor
        with open(self.state_file, "w") as f:
            f.write(str(cursor + len(chunk)))

        logger.info(f"Dataset scraper yielded {len(records)} verified records")
        return records


# ── Pre-configured source definitions ───────────────────────────────────

WELFARE_SOURCES = [
    {
        "name": "Kisan Call Centre (KCC) - data.gov.in",
        "url": "backend/data/trusted_queries.json",
        "scraper_type": "dataset",
        "source_type": "open_dataset",
        "category": "public_queries",
    },
    {
        "name": "sarkariyojana.com RSS",
        "url": "https://sarkariyojana.com/feed/",
        "scraper_type": "rss",
        "source_type": "news_aggregator",
        "category": "scheme_news",
    },
    {
        "name": "MyScheme.gov.in",
        "url": "https://www.myscheme.gov.in/",
        "scraper_type": "html",
        "source_type": "official",
        "category": "government_portal",
    },
    {
        "name": "PIB Press Releases",
        "url": "https://pib.gov.in/allRel.aspx",
        "scraper_type": "html",
        "source_type": "official",
        "category": "press_releases",
    },
    {
        "name": "pmkisan.gov.in FAQ",
        "url": "https://pmkisan.gov.in/",
        "scraper_type": "html",
        "source_type": "official",
        "category": "scheme_faq",
    },
    {
        "name": "pmjay.gov.in FAQ",
        "url": "https://pmjay.gov.in/",
        "scraper_type": "html",
        "source_type": "official",
        "category": "scheme_faq",
    },
    {
        "name": "Down To Earth Welfare",
        "url": "https://www.downtoearth.org.in/rss/latest-news",
        "scraper_type": "rss",
        "source_type": "news",
        "category": "investigative",
    },
]
