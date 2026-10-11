"""
Crawl Engine v2 — Large-scale multi-source data collection platform.

Architecture:
  SourceRegistry → 60+ categorized sources
  DiscoveryEngine → sitemap, RSS, pagination, internal links, topic queries
  CrawlFrontier → URL queue with priority, dedup, retry
  PageFetcher → async HTTP with per-domain rate limiting + retries
  ContentExtractor → document type detection + multi-record extraction
  QuestionExtractor → splits documents into individual Q/complaint records
  CollectionOrchestrator → ties everything together
"""

import asyncio
import hashlib
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Set, Tuple, Any
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.crawl import CrawlUrl, CrawlPage, CollectionCampaign
from backend.app.models.source import Source, SourceRun
from backend.app.models.document import Document
from backend.app.models.audit import AuditLog
from backend.app.services.ingestion import IngestionPipeline

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# EXPANDED SOURCE REGISTRY — 60+ sources across 15 categories
# ═══════════════════════════════════════════════════════════════════════════

SOURCE_REGISTRY: List[Dict] = [
    # ── Verified Real Datasets ────────────────────────────────────────
    {"name": "Kisan Call Centre (KCC) - data.gov.in", "url": "backend/data/trusted_queries.json", "source_type": "open_dataset", "scraper_type": "dataset", "category": "public_queries", "priority": 1},

    # ── Government Open Data ──────────────────────────────────────────
    {"name": "data.gov.in Schemes", "url": "https://data.gov.in/", "source_type": "open_data", "scraper_type": "html", "category": "government_open_data", "priority": 1},
    {"name": "data.gov.in Agriculture", "url": "https://data.gov.in/catalog/agriculture", "source_type": "open_data", "scraper_type": "html", "category": "government_open_data", "priority": 1},

    # ── Central Government Portals ────────────────────────────────────
    {"name": "MyScheme.gov.in", "url": "https://www.myscheme.gov.in/", "source_type": "official", "scraper_type": "html", "category": "central_government", "priority": 1},
    {"name": "india.gov.in Services", "url": "https://www.india.gov.in/topics/agriculture", "source_type": "official", "scraper_type": "html", "category": "central_government", "priority": 1},
    {"name": "PIB Press Releases", "url": "https://pib.gov.in/allRel.aspx", "source_type": "official", "scraper_type": "html", "category": "central_government", "priority": 2},
    {"name": "vikaspedia Schemes", "url": "https://vikaspedia.in/social-welfare/", "source_type": "official", "scraper_type": "html", "category": "central_government", "priority": 1},
    {"name": "vikaspedia Agriculture", "url": "https://vikaspedia.in/agriculture/", "source_type": "official", "scraper_type": "html", "category": "central_government", "priority": 1},

    # ── Official Scheme Websites ──────────────────────────────────────
    {"name": "PM-KISAN Portal", "url": "https://pmkisan.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PM-KISAN"},
    {"name": "PM-JAY Portal", "url": "https://pmjay.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "Ayushman Bharat PM-JAY"},
    {"name": "PMAY Portal", "url": "https://pmaymis.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PMAY"},
    {"name": "MGNREGA Portal", "url": "https://nrega.nic.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "MGNREGA"},
    {"name": "PMFBY Portal", "url": "https://pmfby.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PMFBY"},
    {"name": "PMUY Portal", "url": "https://www.pmuy.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PMUY"},
    {"name": "Mudra Portal", "url": "https://www.mudra.org.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PMMY"},
    {"name": "PM SVANidhi Portal", "url": "https://pmsvanidhi.mohua.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PM SVANidhi"},
    {"name": "PM-KUSUM Portal", "url": "https://pmkusum.mnre.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PM-KUSUM"},
    {"name": "Jan Dhan Portal", "url": "https://pmjdy.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PMJDY"},
    {"name": "PM Vishwakarma Portal", "url": "https://pmvishwakarma.gov.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "PM Vishwakarma"},
    {"name": "NSAP Portal", "url": "https://nsap.nic.in/", "source_type": "official", "scraper_type": "html", "category": "scheme_portal", "priority": 1, "scheme": "NSAP"},

    # ── Agriculture Departments ───────────────────────────────────────
    {"name": "agricoop.nic.in", "url": "https://agricoop.nic.in/", "source_type": "official", "scraper_type": "html", "category": "agriculture", "priority": 2},
    {"name": "icar.org.in", "url": "https://icar.org.in/", "source_type": "official", "scraper_type": "html", "category": "agriculture", "priority": 2},
    {"name": "farmer.gov.in", "url": "https://farmer.gov.in/", "source_type": "official", "scraper_type": "html", "category": "agriculture", "priority": 1},

    # ── Kisan Call Centre / Helpline ──────────────────────────────────
    {"name": "Kisan Call Centre", "url": "https://dackkms.gov.in/", "source_type": "official", "scraper_type": "html", "category": "kisan_helpline", "priority": 1},
    {"name": "KCC Portal", "url": "https://mkisan.gov.in/", "source_type": "official", "scraper_type": "html", "category": "kisan_helpline", "priority": 1},

    # ── News / RSS Sources ────────────────────────────────────────────
    {"name": "sarkariyojana.com RSS", "url": "https://sarkariyojana.com/feed/", "source_type": "news", "scraper_type": "rss", "category": "news_rss", "priority": 2},
    {"name": "sarkariyojana.com", "url": "https://sarkariyojana.com/", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 2},
    {"name": "sarkariresult.com", "url": "https://www.sarkariresult.com/", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 3},
    {"name": "pmmodiyojana.in", "url": "https://pmmodiyojana.in/", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 2},
    {"name": "yojanaschemegov.in", "url": "https://yojanaschemegov.in/", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 2},
    {"name": "indianexpress Govt Schemes", "url": "https://indianexpress.com/about/government-schemes/", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 3},
    {"name": "hindustantimes Schemes", "url": "https://www.hindustantimes.com/topic/government-schemes", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 3},
    {"name": "ndtv Agriculture", "url": "https://www.ndtv.com/topic/government-schemes", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 3},
    {"name": "livemint Policy", "url": "https://www.livemint.com/topic/government-schemes", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 3},
    {"name": "Down To Earth Agriculture", "url": "https://www.downtoearth.org.in/agriculture/", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 2},
    {"name": "Down To Earth RSS", "url": "https://www.downtoearth.org.in/rss/latest-news", "source_type": "news", "scraper_type": "rss", "category": "news_rss", "priority": 2},
    {"name": "economictimes Welfare", "url": "https://economictimes.indiatimes.com/topic/government-welfare-schemes", "source_type": "news", "scraper_type": "html", "category": "news_rss", "priority": 3},

    # ── Public Q&A / Forums ───────────────────────────────────────────
    {"name": "Quora PM-KISAN", "url": "https://www.quora.com/topic/PM-KISAN", "source_type": "forum", "scraper_type": "html", "category": "public_qa", "priority": 3},
    {"name": "Quora Indian Govt Schemes", "url": "https://www.quora.com/topic/Indian-Government-Schemes", "source_type": "forum", "scraper_type": "html", "category": "public_qa", "priority": 3},

    # ── Agriculture Publications ──────────────────────────────────────
    {"name": "krishijagran.com", "url": "https://krishijagran.com/", "source_type": "publication", "scraper_type": "html", "category": "agriculture_pub", "priority": 2},
    {"name": "krishijagran Schemes", "url": "https://krishijagran.com/agriculture-world/government-schemes/", "source_type": "publication", "scraper_type": "html", "category": "agriculture_pub", "priority": 2},
    {"name": "gaonconnection.com", "url": "https://www.gaonconnection.com/", "source_type": "publication", "scraper_type": "html", "category": "agriculture_pub", "priority": 2},
    {"name": "en.gaonconnection.com Schemes", "url": "https://en.gaonconnection.com/tag/government-schemes/", "source_type": "publication", "scraper_type": "html", "category": "agriculture_pub", "priority": 2},
    {"name": "agriwelfare.gov.in", "url": "https://agriwelfare.gov.in/", "source_type": "official", "scraper_type": "html", "category": "agriculture_pub", "priority": 2},

    # ── State Government Portals ──────────────────────────────────────
    {"name": "UP Govt Schemes", "url": "https://up.gov.in/en/page/government-schemes", "source_type": "state_govt", "scraper_type": "html", "category": "state_government", "priority": 2},
    {"name": "MP Govt Schemes", "url": "https://mp.gov.in/schemes", "source_type": "state_govt", "scraper_type": "html", "category": "state_government", "priority": 2},
    {"name": "Bihar Govt Schemes", "url": "https://state.bihar.gov.in/main/CitizenHome.html", "source_type": "state_govt", "scraper_type": "html", "category": "state_government", "priority": 2},
    {"name": "Rajasthan Jan Soochna", "url": "https://jansoochna.rajasthan.gov.in/", "source_type": "state_govt", "scraper_type": "html", "category": "state_government", "priority": 2},
    {"name": "Maharashtra Govt Schemes", "url": "https://www.maharashtra.gov.in/", "source_type": "state_govt", "scraper_type": "html", "category": "state_government", "priority": 3},

    # ── Research / Open Datasets ──────────────────────────────────────
    {"name": "Kaggle Indian Welfare", "url": "https://www.kaggle.com/search?q=indian+government+welfare+scheme", "source_type": "research", "scraper_type": "html", "category": "research", "priority": 4},
    {"name": "HuggingFace Datasets", "url": "https://huggingface.co/datasets?search=indian+government", "source_type": "research", "scraper_type": "html", "category": "research", "priority": 4},

    # ── Wikipedia / Reference ─────────────────────────────────────────
    {"name": "Wikipedia Welfare Schemes", "url": "https://en.wikipedia.org/wiki/Government_welfare_schemes_in_India", "source_type": "reference", "scraper_type": "html", "category": "reference", "priority": 4},
]

# ═══════════════════════════════════════════════════════════════════════════
# SCHEME TOPIC GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

SCHEME_TOPICS = {
    "PM-KISAN": {
        "en": ["eligibility", "application", "registration", "payment", "installment", "status",
               "complaint", "documents", "correction", "Aadhaar", "bank account", "beneficiary",
               "deadline", "rejection", "land records", "eKYC", "amount", "list", "helpline"],
        "hi": ["पात्रता", "आवेदन", "पंजीकरण", "भुगतान", "किस्त", "स्थिति", "शिकायत",
               "दस्तावेज", "सुधार", "आधार", "बैंक खाता", "लाभार्थी", "अंतिम तिथि"],
    },
    "PMFBY": {
        "en": ["crop insurance", "premium", "claim", "enrollment", "season", "coverage",
               "Kharif", "Rabi", "notification", "subsidy", "loss assessment", "complaint"],
        "hi": ["फसल बीमा", "प्रीमियम", "दावा", "नामांकन", "मौसम", "कवरेज"],
    },
    "PMAY": {
        "en": ["housing", "subsidy", "eligibility", "application", "beneficiary", "urban",
               "rural", "Gramin", "CLSS", "interest subsidy", "construction", "loan"],
        "hi": ["आवास", "सब्सिडी", "पात्रता", "आवेदन", "लाभार्थी", "ग्रामीण"],
    },
    "Ayushman Bharat PM-JAY": {
        "en": ["health insurance", "hospital", "eligibility", "card", "treatment", "cashless",
               "empanelled hospital", "claim", "coverage", "family", "beneficiary", "complaint"],
        "hi": ["स्वास्थ्य बीमा", "अस्पताल", "पात्रता", "कार्ड", "इलाज", "कैशलेस"],
    },
    "MGNREGA": {
        "en": ["job card", "employment", "wages", "100 days", "work", "attendance",
               "payment", "complaint", "registration", "muster roll", "gram panchayat"],
        "hi": ["जॉब कार्ड", "रोजगार", "मजदूरी", "100 दिन", "काम", "उपस्थिति", "भुगतान"],
    },
    "PMUY": {
        "en": ["LPG", "gas connection", "free cylinder", "refill", "subsidy", "eligibility",
               "application", "BPL", "beneficiary", "complaint"],
        "hi": ["एलपीजी", "गैस कनेक्शन", "मुफ्त सिलेंडर", "रिफिल", "सब्सिडी"],
    },
    "PMMY": {
        "en": ["Mudra loan", "Shishu", "Kishore", "Tarun", "eligibility", "application",
               "bank", "interest rate", "repayment", "rejection", "MSME"],
        "hi": ["मुद्रा ऋण", "शिशु", "किशोर", "तरुण", "पात्रता", "बैंक"],
    },
    "PM SVANidhi": {
        "en": ["street vendor", "loan", "eligibility", "application", "repayment",
               "digital payment", "interest subsidy", "certificate of vending"],
    },
    "PMJDY": {
        "en": ["Jan Dhan", "zero balance", "bank account", "RuPay card", "overdraft",
               "insurance", "eligibility", "application", "beneficiary"],
    },
    "PM-KUSUM": {
        "en": ["solar pump", "solar energy", "farmer", "eligibility", "subsidy",
               "application", "component A", "component B", "component C"],
    },
    "APY": {
        "en": ["Atal Pension", "pension", "eligibility", "contribution", "age",
               "withdrawal", "bank", "nominee"],
    },
    "PMJJBY": {
        "en": ["Jeevan Jyoti", "life insurance", "premium", "claim", "coverage",
               "eligibility", "renewal", "bank"],
    },
    "PMSBY": {
        "en": ["Suraksha Bima", "accident insurance", "premium", "claim", "coverage",
               "eligibility", "renewal"],
    },
    "NSAP": {
        "en": ["old age pension", "widow pension", "disability pension", "social assistance",
               "eligibility", "application", "amount", "BPL"],
    },
    "PM Vishwakarma": {
        "en": ["artisan", "craftsman", "toolkit", "training", "loan", "eligibility",
               "application", "certificate", "recognition"],
    },
}


def generate_search_queries(scheme: str, max_queries: int = 20) -> List[str]:
    """Generate search queries for a scheme across its topics."""
    topics = SCHEME_TOPICS.get(scheme, {})
    queries = []
    for lang, topic_list in topics.items():
        for topic in topic_list:
            if lang == "en":
                queries.append(f"{scheme} {topic}")
                queries.append(f"{scheme} {topic} India")
            else:
                queries.append(f"{scheme} {topic}")
    return queries[:max_queries]


# ═══════════════════════════════════════════════════════════════════════════
# DISCOVERY ENGINE — sitemap, RSS, pagination, internal links
# ═══════════════════════════════════════════════════════════════════════════

class DiscoveryEngine:
    """Discovers URLs from a domain via sitemap, RSS, pagination, and internal links."""

    WELFARE_KEYWORDS = [
        "scheme", "yojana", "welfare", "subsidy", "beneficiary", "eligibility",
        "application", "registration", "pm-kisan", "pmkisan", "pmay", "pmjay",
        "ayushman", "mgnrega", "nrega", "mudra", "svanidhi", "ujjwala", "kusum",
        "jan-dhan", "pmjdy", "fasal-bima", "pmfby", "pension", "kisan", "farmer",
        "agriculture", "rural", "faq", "question", "complaint", "grievance",
        "helpline", "guideline", "document", "apply", "status", "payment",
        "insurance", "loan", "housing", "awas", "bima", "vishwakarma",
    ]

    def __init__(self, client: httpx.Client):
        self.client = client
        self._seen_urls: Set[str] = set()

    def _is_relevant_url(self, url: str) -> bool:
        """Check if a URL is likely relevant to welfare schemes."""
        url_lower = url.lower()
        # Skip obvious non-content
        skip_patterns = [
            "/wp-content/", "/wp-admin/", "/wp-includes/",
            ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
            ".woff", ".ttf", ".mp4", ".mp3", "/feed/", "/rss/",
            "/login", "/signup", "/register", "/cart", "/checkout",
            "/privacy", "/terms", "/disclaimer", "/sitemap.xml",
            "#", "javascript:", "mailto:", "tel:",
        ]
        for pat in skip_patterns:
            if pat in url_lower:
                return False
        # Check for relevant keywords
        for kw in self.WELFARE_KEYWORDS:
            if kw in url_lower:
                return True
        # For known welfare domains, accept most URLs
        welfare_domains = [
            "pmkisan", "pmjay", "pmay", "mgnrega", "nrega", "pmfby",
            "pmuy", "mudra", "svanidhi", "pmjdy", "vikaspedia",
            "myscheme", "sarkariyojana", "pmmodiyojana", "krishijagran",
            "gaonconnection", "farmer.gov", "agriwelfare",
        ]
        parsed = urlparse(url)
        for d in welfare_domains:
            if d in parsed.netloc:
                return True
        return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        if isinstance(url, bytes):
            url = url.decode('utf-8', errors='replace')
        if not url:
            return ""
        parsed = urlparse(url)
        # Remove fragment, trailing slash
        clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'),
                           '', parsed.query, ''))
        return clean

    def discover_sitemap(self, base_url: str, max_urls: int = 500) -> List[str]:
        """Discover URLs from sitemap.xml and sitemap indexes."""
        parsed = urlparse(base_url)
        sitemap_candidates = [
            f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap-index.xml",
            f"{parsed.scheme}://{parsed.netloc}/wp-sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/post-sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/page-sitemap.xml",
        ]

        urls = []
        for sitemap_url in sitemap_candidates:
            try:
                resp = self.client.get(sitemap_url, timeout=15)
                if resp.status_code != 200:
                    continue
                urls.extend(self._parse_sitemap(resp.text, max_urls - len(urls)))
                if len(urls) >= max_urls:
                    break
            except Exception as e:
                logger.debug(f"Sitemap fetch failed for {sitemap_url}: {e}")
                continue

        relevant = [u for u in urls if self._is_relevant_url(u)]
        logger.info(f"Sitemap discovery: {len(urls)} total, {len(relevant)} relevant from {parsed.netloc}")
        return relevant[:max_urls]

    def _parse_sitemap(self, xml_content: str, max_urls: int = 500) -> List[str]:
        """Parse sitemap XML, handling both index and regular sitemaps."""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Check if this is a sitemap index
            for sitemap in root.findall('.//sm:sitemap/sm:loc', ns):
                if len(urls) >= max_urls:
                    break
                try:
                    resp = self.client.get(sitemap.text.strip(), timeout=15)
                    if resp.status_code == 200:
                        urls.extend(self._parse_sitemap(resp.text, max_urls - len(urls)))
                except Exception:
                    continue

            # Regular sitemap URLs
            for loc in root.findall('.//sm:url/sm:loc', ns):
                if len(urls) >= max_urls:
                    break
                urls.append(loc.text.strip())
        except ET.ParseError:
            logger.debug("Failed to parse sitemap XML")
        return urls

    def discover_rss(self, url: str, max_urls: int = 100) -> List[str]:
        """Discover article URLs from RSS/Atom feeds."""
        try:
            import feedparser
            resp = self.client.get(url, timeout=15)
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            urls = []
            for entry in feed.entries[:max_urls]:
                link = getattr(entry, 'link', None)
                if link and self._is_relevant_url(link):
                    urls.append(link)
            logger.info(f"RSS discovery: {len(urls)} URLs from {url}")
            return urls
        except Exception as e:
            logger.debug(f"RSS discovery failed for {url}: {e}")
            return []

    def discover_pagination(self, url: str, html: str, max_pages: int = 20) -> List[str]:
        """Discover paginated URLs from HTML."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        urls = []

        # Strategy 1: Look for pagination links
        pagination_selectors = [
            "nav.pagination a", "div.pagination a", "ul.pagination a",
            "a.page-numbers", "a[class*='paginat']", "a[class*='page-link']",
            "a[rel='next']",
        ]
        for selector in pagination_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    abs_url = urljoin(url, href)
                    if abs_url not in self._seen_urls:
                        urls.append(abs_url)
                        self._seen_urls.add(abs_url)

        # Strategy 2: Generate page URLs from patterns
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if not urls:
            for page_num in range(2, max_pages + 1):
                # Try ?page=N
                page_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?page={page_num}"
                urls.append(page_url)
                # Try /page/N/
                if '/page/' not in parsed.path:
                    page_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/page/{page_num}/"
                    urls.append(page_url)

        logger.info(f"Pagination discovery: {len(urls)} candidate pages from {url}")
        return urls[:max_pages * 2]

    def discover_internal_links(self, url: str, html: str, max_depth: int = 2,
                                 current_depth: int = 0) -> List[Tuple[str, int]]:
        """Extract relevant internal links with depth tracking."""
        if current_depth >= max_depth:
            return []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        parsed_base = urlparse(url)
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            abs_url = urljoin(url, href)
            parsed = urlparse(abs_url)

            # Same domain only
            if parsed.netloc != parsed_base.netloc:
                continue

            normalized = self._normalize_url(abs_url)
            if normalized in self._seen_urls:
                continue

            if self._is_relevant_url(abs_url):
                self._seen_urls.add(normalized)
                links.append((normalized, current_depth + 1))

        logger.info(f"Internal link discovery: {len(links)} relevant links from {url} (depth {current_depth})")
        return links


# ═══════════════════════════════════════════════════════════════════════════
# QUESTION / RECORD EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════

class QuestionExtractor:
    """Extracts individual questions, complaints, and awareness-gap signals from text."""

    QUESTION_PATTERNS = [
        r'[^.!?\n]*\?',  # Sentences ending with ?
        r'(?:what|why|how|can\s+i|am\s+i|where\s+can|when\s+will|how\s+much|how\s+to|'
        r'what\s+documents|what\s+is|who\s+is|which|is\s+it|do\s+i|will\s+i|'
        r'when\s+is|how\s+many|how\s+long)[^.!?\n]*[.!?\n]',
        r'(?:kya|kaise|kab|kahan|kyun|kitna|kaun)[^.!?\n]*[.!?\n]',  # Hindi question words
    ]

    COMPLAINT_PATTERNS = [
        r"(?:haven't|have\s+not|didn't|did\s+not)\s+(?:received?|got)\s+[^.!?\n]*[.!?\n]",
        r'(?:not\s+(?:received?|got|working|eligible|approved)|rejected|delayed|pending|failed)[^.!?\n]*[.!?\n]',
        r'(?:problem|issue|complaint|grievance|difficulty|trouble|unable|cannot|can\'t)[^.!?\n]*[.!?\n]',
        r'(?:nahi\s+mila|nahi\s+aaya|koi\s+jawab\s+nahi|samajh\s+nahi)[^.!?\n]*[.!?\n]',
    ]

    MIN_QUESTION_LENGTH = 15
    MAX_QUESTION_LENGTH = 1000

    @classmethod
    def extract_from_text(cls, text: str, source_url: str = "",
                          source_name: str = "", scheme: Optional[str] = None) -> List[Dict]:
        """Extract individual question/complaint records from a block of text."""
        records = []
        seen = set()

        # Extract questions
        for pattern in cls.QUESTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                q = match.group(0).strip()
                if cls._is_valid_record(q) and q.lower() not in seen:
                    seen.add(q.lower())
                    records.append({
                        "text": q,
                        "text_role": "question",
                        "source_url": source_url,
                        "source_name": source_name,
                        "scheme_name": scheme,
                        "extraction_method": "question_pattern",
                    })

        # Extract complaints
        for pattern in cls.COMPLAINT_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                c = match.group(0).strip()
                if cls._is_valid_record(c) and c.lower() not in seen:
                    seen.add(c.lower())
                    records.append({
                        "text": c,
                        "text_role": "complaint",
                        "source_url": source_url,
                        "source_name": source_name,
                        "scheme_name": scheme,
                        "extraction_method": "complaint_pattern",
                    })

        return records

    @classmethod
    def _is_valid_record(cls, text: str) -> bool:
        if len(text) < cls.MIN_QUESTION_LENGTH or len(text) > cls.MAX_QUESTION_LENGTH:
            return False
        # Skip navigation/boilerplate
        boilerplate = [
            "click here", "read more", "subscribe", "sign up", "log in",
            "cookie", "privacy policy", "terms of service", "copyright",
            "advertisement", "loading", "share this",
        ]
        text_lower = text.lower()
        for bp in boilerplate:
            if bp in text_lower and len(text) < 60:
                return False
        return True


# ═══════════════════════════════════════════════════════════════════════════
# CONTENT EXTRACTOR — multi-record extraction from HTML
# ═══════════════════════════════════════════════════════════════════════════

class ContentExtractor:
    """Extracts structured content from HTML pages with multi-record support."""

    SCHEME_KEYWORDS = {
        "PM-KISAN": ["pm-kisan", "pm kisan", "kisan samman", "kisan nidhi", "pmkisan"],
        "PMAY": ["pmay", "awas yojana", "pradhan mantri awas"],
        "Ayushman Bharat PM-JAY": ["ayushman", "pm-jay", "pmjay", "jan arogya"],
        "MGNREGA": ["mgnrega", "mnrega", "nrega", "mahatma gandhi national rural", "job card"],
        "PMUY": ["pmuy", "ujjwala", "ujjawala"],
        "PMFBY": ["pmfby", "fasal bima", "crop insurance"],
        "PMMY": ["pmmy", "mudra", "mudra loan"],
        "PM SVANidhi": ["svanidhi", "pm svanidhi", "street vendor"],
        "PMJDY": ["pmjdy", "jan dhan", "jan-dhan"],
        "PM-KUSUM": ["kusum", "pm-kusum", "solar pump"],
        "APY": ["atal pension", "apy"],
        "PMJJBY": ["pmjjby", "jeevan jyoti"],
        "PMSBY": ["pmsby", "suraksha bima"],
        "NSAP": ["nsap", "social assistance", "old age pension", "widow pension"],
        "PM Vishwakarma": ["vishwakarma", "pm vishwakarma"],
    }

    @classmethod
    def detect_scheme(cls, text: str) -> Optional[str]:
        text_lower = text.lower()
        for scheme, keywords in cls.SCHEME_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return scheme
        return None

    @classmethod
    def extract_from_html(cls, html: str, url: str, source_name: str = "") -> List[Dict]:
        """Extract multiple records from an HTML page."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        records = []

        # Remove noise
        for tag in soup.select("script, style, nav, header, footer, aside, .sidebar, .menu, .ad, .advertisement"):
            tag.decompose()

        page_title = soup.title.string if soup.title else ""
        page_scheme = cls.detect_scheme(page_title + " " + url)

        # Strategy 1: FAQ / Accordion blocks → individual Q&A records
        faq_selectors = [
            "details", "div.faq-item", "div[class*='faq']", "div.accordion-item",
            "div[class*='question']", "div[class*='accordion']",
            "div[itemtype*='Question']", "div[itemtype*='FAQPage']",
            "dt", "h3.faq-question", "h4.faq-question",
        ]
        for selector in faq_selectors:
            for block in soup.select(selector):
                text = block.get_text(separator=" ", strip=True)
                if 20 < len(text) < 2000:
                    scheme = cls.detect_scheme(text) or page_scheme
                    records.append({
                        "text": text, "source_url": url, "source_name": source_name,
                        "scheme_name": scheme, "text_role": "faq",
                        "extraction_method": "html_faq", "page_title": page_title,
                    })

        # Strategy 2: Comments / user-generated content
        comment_selectors = [
            "div.comment-body", "div[class*='comment-content']",
            "div.post-content", "div[class*='reply-body']",
            "div[class*='user-content']", "div[class*='discussion']",
            "article.comment", "li.comment",
        ]
        for selector in comment_selectors:
            for block in soup.select(selector):
                text = block.get_text(separator=" ", strip=True)
                if 30 < len(text) < 3000:
                    scheme = cls.detect_scheme(text) or page_scheme
                    records.append({
                        "text": text, "source_url": url, "source_name": source_name,
                        "scheme_name": scheme, "text_role": "discussion",
                        "extraction_method": "html_comment", "page_title": page_title,
                    })

        # Strategy 3: Article paragraphs → split into questions if multi-Q
        if len(records) < 3:
            article_text = ""
            for tag in ["article", "main", "div[class*='entry-content']",
                        "div[class*='post-content']", "div[class*='article-body']",
                        "div.content", "div[role='main']"]:
                for block in soup.select(tag):
                    article_text += " " + block.get_text(separator=" ", strip=True)

            if len(article_text) > 100:
                scheme = cls.detect_scheme(article_text) or page_scheme
                # Try to split into individual questions
                sub_records = QuestionExtractor.extract_from_text(
                    article_text, source_url=url, source_name=source_name, scheme=scheme
                )
                if sub_records:
                    records.extend(sub_records)
                elif len(article_text.strip()) > 50:
                    # Keep as a single article record
                    records.append({
                        "text": article_text.strip()[:5000],
                        "source_url": url, "source_name": source_name,
                        "scheme_name": scheme, "text_role": "article",
                        "extraction_method": "html_article", "page_title": page_title,
                    })

        # Strategy 4: All paragraphs with scheme keywords (fallback)
        if len(records) == 0:
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 50:
                    scheme = cls.detect_scheme(text)
                    if scheme:
                        records.append({
                            "text": text, "source_url": url, "source_name": source_name,
                            "scheme_name": scheme, "text_role": "paragraph",
                            "extraction_method": "html_paragraph", "page_title": page_title,
                        })

        return records

    @classmethod
    def extract_from_rss(cls, feed_content: str, feed_url: str,
                          source_name: str = "") -> List[Dict]:
        """Extract records from RSS feed, with article link discovery."""
        import feedparser
        feed = feedparser.parse(feed_content)
        records = []
        article_urls = []

        for entry in feed.entries:
            title = getattr(entry, 'title', '')
            summary = getattr(entry, 'summary', '')
            link = getattr(entry, 'link', feed_url)
            published = getattr(entry, 'published', '')

            text = f"{title}. {summary}".strip('. ')
            if len(text) < 15:
                continue

            scheme = cls.detect_scheme(text)
            records.append({
                "text": text, "source_url": link, "source_name": source_name,
                "scheme_name": scheme, "text_role": "news",
                "extraction_method": "rss",
                "metadata": {"title": title, "published": published, "feed_url": feed_url},
            })

            # Collect article URLs for deeper crawling
            if link and link != feed_url:
                article_urls.append(link)

        return records, article_urls


# ═══════════════════════════════════════════════════════════════════════════
# PAGE FETCHER — async HTTP with retries, per-domain rate limiting
# ═══════════════════════════════════════════════════════════════════════════

class PageFetcher:
    """Fetches pages with retries, rate limiting, and content-hash change detection."""

    RETRY_STATUSES = {408, 429, 500, 502, 503, 504}
    MAX_RETRIES = 3

    def __init__(self, crawl_delay: float = 2.0, timeout: float = 30.0):
        self.crawl_delay = crawl_delay
        self.timeout = timeout
        self._last_request: Dict[str, float] = {}
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "WelfareGapMiner-Academic/2.0 (+research; respectful-crawling)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
                },
            )
        return self._client

    def _rate_limit(self, domain: str, delay: float):
        now = time.time()
        last = self._last_request.get(domain, 0)
        wait = delay - (now - last)
        if wait > 0:
            time.sleep(wait)
        self._last_request[domain] = time.time()

    def fetch(self, url: str, delay: Optional[float] = None) -> Tuple[Optional[str], int, Optional[str]]:
        """Fetch URL with retries. Returns (content, http_status, content_hash)."""
        domain = urlparse(url).netloc
        d = delay or self.crawl_delay

        for attempt in range(1, self.MAX_RETRIES + 1):
            self._rate_limit(domain, d)
            try:
                resp = self.client.get(url)
                content = resp.text
                h = hashlib.sha256(content.encode('utf-8', errors='replace')).hexdigest()[:16]

                if resp.status_code == 200:
                    return content, resp.status_code, h
                elif resp.status_code in self.RETRY_STATUSES and attempt < self.MAX_RETRIES:
                    wait = min(2 ** attempt, 30)
                    logger.warning(f"Retry {attempt}/{self.MAX_RETRIES} for {url} (HTTP {resp.status_code}), waiting {wait}s")
                    time.sleep(wait)
                    continue
                else:
                    return None, resp.status_code, None
            except Exception as e:
                if attempt < self.MAX_RETRIES:
                    wait = min(2 ** attempt, 30)
                    logger.warning(f"Retry {attempt}/{self.MAX_RETRIES} for {url} ({e}), waiting {wait}s")
                    time.sleep(wait)
                else:
                    logger.error(f"Failed after {self.MAX_RETRIES} attempts: {url} — {e}")
                    return None, 0, None
        return None, 0, None

    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ═══════════════════════════════════════════════════════════════════════════
# COLLECTION ORCHESTRATOR v2
# ═══════════════════════════════════════════════════════════════════════════

class CollectionOrchestrator:
    """Orchestrates large-scale multi-source collection campaigns."""

    def __init__(self, db: Session):
        self.db = db
        self.fetcher = PageFetcher()
        self.pipeline = IngestionPipeline()

    def register_all_sources(self) -> List[Source]:
        """Register all sources from SOURCE_REGISTRY."""
        from backend.app.services.scraper import PolicyEngine
        policy_engine = PolicyEngine()
        sources = []

        for src in SOURCE_REGISTRY:
            existing = self.db.query(Source).filter(Source.url == src["url"]).first()
            if existing:
                sources.append(existing)
                continue

            policy = policy_engine.check_robots(src["url"])
            source = Source(
                name=src["name"],
                url=src["url"],
                source_type=src.get("source_type", "web"),
                collection_method="scraper",
                content_type=src.get("scraper_type", "html"),
                description=src.get("category", ""),
                policy_status="allowed" if policy["allowed"] else "blocked",
                robots_checked=policy["robots_checked"],
                crawl_delay=policy.get("crawl_delay", 2.0),
                active=policy["allowed"],
            )
            self.db.add(source)
            sources.append(source)

        self.db.commit()
        self._audit("sources_registered", "system", "bulk", f"Registered {len(sources)} sources")
        return sources

    def create_campaign(self, name: str, schemes: Optional[List[str]] = None,
                        max_urls: int = 5000, max_depth: int = 3,
                        max_pages_per_source: int = 200) -> CollectionCampaign:
        """Create a new collection campaign."""
        campaign = CollectionCampaign(
            name=name,
            schemes=schemes or list(SCHEME_TOPICS.keys()),
            topics=[],
            max_urls=max_urls,
            max_depth=max_depth,
            max_pages_per_source=max_pages_per_source,
            status="created",
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def run_campaign(self, campaign_id: int) -> Dict:
        """Execute a full collection campaign: discover → crawl → extract → store."""
        campaign = self.db.query(CollectionCampaign).filter(CollectionCampaign.id == campaign_id).first()
        if not campaign:
            return {"error": "Campaign not found"}

        campaign.status = "discovering"
        campaign.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            # Phase 1: Discovery
            logger.info(f"Campaign '{campaign.name}': starting discovery phase")
            discovery_stats = self._discover_urls(campaign)

            # Phase 2: Collection
            campaign.status = "collecting"
            self.db.commit()
            logger.info(f"Campaign '{campaign.name}': starting collection phase ({campaign.urls_accepted} URLs)")
            collection_stats = self._collect_pages(campaign)

            # Phase 3: Extraction + Storage
            campaign.status = "processing"
            self.db.commit()
            logger.info(f"Campaign '{campaign.name}': starting extraction phase")
            extraction_stats = self._extract_and_store(campaign)

            campaign.status = "completed"
            campaign.finished_at = datetime.now(timezone.utc)
            self.db.commit()

            result = {
                "status": "completed",
                "campaign_id": campaign.id,
                "discovery": discovery_stats,
                "collection": collection_stats,
                "extraction": extraction_stats,
                "final_metrics": {
                    "urls_discovered": campaign.urls_discovered,
                    "urls_accepted": campaign.urls_accepted,
                    "pages_downloaded": campaign.pages_downloaded,
                    "pages_useful": campaign.pages_useful,
                    "records_extracted": campaign.records_extracted,
                    "records_duplicate": campaign.records_duplicate,
                    "records_rejected": campaign.records_rejected,
                    "records_final": campaign.records_final,
                },
            }
            self._audit("campaign_completed", "campaign", str(campaign.id),
                        f"Campaign '{campaign.name}': {campaign.records_final} final records")
            return result

        except Exception as e:
            campaign.status = "failed"
            campaign.finished_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.error(f"Campaign '{campaign.name}' failed: {e}", exc_info=True)
            self._audit("campaign_failed", "campaign", str(campaign.id), str(e), severity="error")
            return {"error": str(e), "campaign_id": campaign.id}

    # ── Phase 1: URL Discovery ────────────────────────────────────────

    def _discover_urls(self, campaign: CollectionCampaign) -> Dict:
        """Discover URLs from all active sources via sitemap, RSS, pagination, links."""
        discovery = DiscoveryEngine(self.fetcher.client)
        sources = self.db.query(Source).filter(
            Source.active == True, Source.policy_status != "blocked"
        ).all()

        total_discovered = 0
        total_accepted = 0

        for source in sources:
            if not source.url:
                continue
            if total_accepted >= (campaign.max_urls or 5000):
                break

            source_urls = []
            parsed = urlparse(source.url)

            # 1. Sitemap discovery
            sitemap_urls = discovery.discover_sitemap(
                source.url, max_urls=campaign.max_pages_per_source or 200
            )
            for u in sitemap_urls:
                source_urls.append((u, "sitemap", 1))

            # 2. RSS discovery (if RSS type)
            if source.content_type == "rss":
                rss_urls = discovery.discover_rss(source.url)
                for u in rss_urls:
                    source_urls.append((u, "rss", 1))

            # 3. Homepage + internal links
            content, status, _ = self.fetcher.fetch(source.url, delay=source.crawl_delay or 2.0)
            if content and status == 200:
                # Pagination
                page_urls = discovery.discover_pagination(source.url, content, max_pages=10)
                for u in page_urls:
                    source_urls.append((u, "pagination", 1))

                # Internal links
                internal = discovery.discover_internal_links(source.url, content, max_depth=campaign.max_depth or 3)
                for u, depth in internal:
                    source_urls.append((u, "internal_link", depth))

            # 4. Always include the source URL itself
            source_urls.insert(0, (source.url, "manual", 0))

            # Deduplicate and store
            seen = set()
            for url_str, method, depth in source_urls:
                if total_accepted >= (campaign.max_urls or 5000):
                    break
                normalized = discovery._normalize_url(url_str)
                if normalized in seen:
                    continue
                seen.add(normalized)

                existing = self.db.query(CrawlUrl).filter(
                    CrawlUrl.url == normalized, CrawlUrl.campaign_id == campaign.id
                ).first()
                if existing:
                    continue

                priority = 3 if depth == 0 else (5 if depth == 1 else 7)
                crawl_url = CrawlUrl(
                    source_id=source.id,
                    campaign_id=campaign.id,
                    url=normalized,
                    domain=parsed.netloc,
                    discovered_from=source.url if method != "manual" else None,
                    discovery_method=method,
                    depth=depth,
                    priority=priority,
                    status="queued",
                )
                self.db.add(crawl_url)
                total_discovered += 1
                total_accepted += 1

            self.db.commit()
            logger.info(f"Source '{source.name}': {len(seen)} URLs queued")

        campaign.urls_discovered = total_discovered
        campaign.urls_accepted = total_accepted
        self.db.commit()

        return {"total_discovered": total_discovered, "total_accepted": total_accepted, "sources_processed": len(sources)}

    # ── Phase 2: Page Collection ──────────────────────────────────────

    def _collect_pages(self, campaign: CollectionCampaign) -> Dict:
        """Download all queued URLs, store as CrawlPage."""
        queued_urls = (
            self.db.query(CrawlUrl)
            .filter(CrawlUrl.campaign_id == campaign.id, CrawlUrl.status == "queued")
            .order_by(CrawlUrl.priority, CrawlUrl.depth)
            .all()
        )

        downloaded = 0
        failed = 0
        blocked = 0

        for crawl_url in queued_urls:
            crawl_url.status = "processing"
            crawl_url.attempt_count += 1
            crawl_url.last_attempt_at = datetime.now(timezone.utc)

            # Get source crawl delay
            source = self.db.query(Source).filter(Source.id == crawl_url.source_id).first()
            delay = source.crawl_delay if source else 2.0

            content, http_status, content_hash = self.fetcher.fetch(crawl_url.url, delay=delay)

            crawl_url.http_status = http_status
            crawl_url.content_hash = content_hash

            if content and http_status == 200:
                crawl_url.status = "success"
                crawl_url.content_length = len(content)

                # Store page
                page = CrawlPage(
                    crawl_url_id=crawl_url.id,
                    source_id=crawl_url.source_id,
                    campaign_id=campaign.id,
                    url=crawl_url.url,
                    http_status=http_status,
                    content_hash=content_hash,
                    content_length=len(content),
                    fetched_at=datetime.now(timezone.utc),
                )
                self.db.add(page)
                downloaded += 1

                # Also discover internal links from this page (depth+1)
                if crawl_url.depth < (campaign.max_depth or 3):
                    disc = DiscoveryEngine(self.fetcher.client)
                    disc._seen_urls = {u.url for u in self.db.query(CrawlUrl.url).filter(
                        CrawlUrl.campaign_id == campaign.id
                    ).all()}
                    new_links = disc.discover_internal_links(
                        crawl_url.url, content,
                        max_depth=(campaign.max_depth or 3),
                        current_depth=crawl_url.depth
                    )
                    for link_url, link_depth in new_links[:20]:  # Cap per-page
                        existing = self.db.query(CrawlUrl).filter(
                            CrawlUrl.url == link_url, CrawlUrl.campaign_id == campaign.id
                        ).first()
                        if not existing:
                            new_crawl = CrawlUrl(
                                source_id=crawl_url.source_id,
                                campaign_id=campaign.id,
                                url=link_url,
                                domain=crawl_url.domain,
                                discovered_from=crawl_url.url,
                                discovery_method="internal_link",
                                depth=link_depth,
                                priority=7,
                                status="queued",
                            )
                            self.db.add(new_crawl)
            elif http_status in (403, 401):
                crawl_url.status = "blocked"
                blocked += 1
            else:
                crawl_url.status = "failed"
                crawl_url.error_message = f"HTTP {http_status}"
                failed += 1

            # Commit every 10 URLs
            if (downloaded + failed + blocked) % 10 == 0:
                self.db.commit()

        campaign.pages_downloaded = downloaded
        self.db.commit()

        return {"downloaded": downloaded, "failed": failed, "blocked": blocked}

    # ── Phase 3: Extraction + Storage ─────────────────────────────────

    def _extract_and_store(self, campaign: CollectionCampaign) -> Dict:
        """Extract records from downloaded pages, run through ingestion, store as Documents."""
        pages = (
            self.db.query(CrawlPage)
            .filter(CrawlPage.campaign_id == campaign.id, CrawlPage.processed_at == None)
            .all()
        )

        all_records = []
        pages_useful = 0

        for page in pages:
            # Re-fetch content (we don't store raw HTML in DB to save space)
            content, status, _ = self.fetcher.fetch(page.url, delay=1.0)
            if not content or status != 200:
                page.has_useful_content = False
                page.processed_at = datetime.now(timezone.utc)
                continue

            # Detect page type and extract
            source = self.db.query(Source).filter(Source.id == page.source_id).first()
            source_name = source.name if source else ""

            if page.url.endswith('.xml') or 'rss' in page.url or 'feed' in page.url:
                # RSS extraction
                try:
                    records, _ = ContentExtractor.extract_from_rss(content, page.url, source_name)
                    page.page_type = "rss"
                except Exception:
                    records = []
            else:
                # HTML extraction
                records = ContentExtractor.extract_from_html(content, page.url, source_name)
                page.page_type = "article" if records else "unknown"

            page.records_extracted = len(records)
            page.has_useful_content = len(records) > 0
            page.processed_at = datetime.now(timezone.utc)

            if records:
                pages_useful += 1
                all_records.extend(records)

        # Run all records through ingestion pipeline
        pipeline_result = self.pipeline.process_records([
            {"text": r.get("text", ""), "scheme_name": r.get("scheme_name"),
             "source_name": r.get("source_name"), "source_url": r.get("source_url"),
             "source_type": r.get("extraction_method", "web")}
            for r in all_records
        ])

        # Store valid records
        stored = 0
        for rec in pipeline_result["valid_records"]:
            doc = Document(
                original_text=rec["text"],
                normalized_text=rec.get("normalized_text"),
                scheme_name=rec.get("scheme_name"),
                source_name=rec.get("source_name"),
                source_type=rec.get("source_type", "web"),
                source_url=rec.get("source_url"),
                language="English",
                processing_status="imported",
                pii_detected=rec.get("pii_detected", False),
                pii_redacted=rec.get("pii_redacted", False),
                is_duplicate=rec.get("is_duplicate", False),
                is_synthetic=False,
                is_demo=False,
                collected_at=datetime.now(timezone.utc),
            )
            self.db.add(doc)
            stored += 1

        campaign.pages_useful = pages_useful
        campaign.records_extracted = len(all_records)
        campaign.records_duplicate = len(pipeline_result["duplicate_records"])
        campaign.records_rejected = len(pipeline_result["rejected_records"])
        campaign.records_final = stored
        self.db.commit()

        return {
            "pages_processed": len(pages),
            "pages_useful": pages_useful,
            "records_extracted": len(all_records),
            "records_duplicate": len(pipeline_result["duplicate_records"]),
            "records_rejected": len(pipeline_result["rejected_records"]),
            "records_stored": stored,
        }

    # ── Utility ───────────────────────────────────────────────────────

    def get_campaign_funnel(self, campaign_id: int) -> Dict:
        """Pipeline diagnostic — shows exactly where records are gained/lost."""
        campaign = self.db.query(CollectionCampaign).filter(CollectionCampaign.id == campaign_id).first()
        if not campaign:
            return {"error": "Campaign not found"}

        return {
            "campaign": campaign.name,
            "status": campaign.status,
            "funnel": [
                {"stage": "URLs Discovered", "count": campaign.urls_discovered},
                {"stage": "URLs Accepted", "count": campaign.urls_accepted},
                {"stage": "Pages Downloaded", "count": campaign.pages_downloaded},
                {"stage": "Pages With Content", "count": campaign.pages_useful},
                {"stage": "Candidate Records", "count": campaign.records_extracted},
                {"stage": "Duplicates Removed", "count": campaign.records_duplicate, "delta": True},
                {"stage": "Rejected (Quality)", "count": campaign.records_rejected, "delta": True},
                {"stage": "Final Records", "count": campaign.records_final, "highlight": True},
            ],
        }

    def _audit(self, action: str, entity_type: str, entity_id: str,
               description: str, severity: str = "info"):
        log = AuditLog(
            action=action, entity_type=entity_type, entity_id=entity_id,
            description=description, user="collector", severity=severity,
        )
        self.db.add(log)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
