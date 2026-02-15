"""
News fetcher module - retrieves news from multiple Italian and international sources.
"""

import logging
import time
import urllib.parse
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}


def _parse_date(entry):
    """Extract and normalize publication date from a feed entry."""
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _clean_html(raw_html):
    """Strip HTML tags from a string."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def fetch_google_news(company_name, keywords, config):
    """Search Google News RSS for a company."""
    source_cfg = config.get("sources", {}).get("google_news", {})
    if not source_cfg.get("enabled", True):
        return []

    base_url = source_cfg.get("base_url", "https://news.google.com/rss/search")
    lang = source_cfg.get("language", "it")
    country = source_cfg.get("country", "IT")

    articles = []
    for keyword in keywords:
        query = urllib.parse.quote(keyword)
        url = f"{base_url}?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"

        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
            for entry in feed.entries:
                articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": _parse_date(entry),
                    "summary": _clean_html(entry.get("summary", "")),
                    "source": "Google News",
                    "company": company_name,
                })
        except Exception as e:
            logger.warning("Error fetching Google News for %s: %s", keyword, e)

    return articles


def fetch_rss_feed(feed_url, source_name, company_name, keywords):
    """Fetch articles from an RSS feed and filter by company keywords."""
    articles = []
    try:
        feed = feedparser.parse(feed_url, agent=USER_AGENT)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = _clean_html(entry.get("summary", ""))
            text = f"{title} {summary}".lower()

            # Check if any keyword matches
            if any(kw.lower() in text for kw in keywords):
                articles.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": _parse_date(entry),
                    "summary": summary,
                    "source": source_name,
                    "company": company_name,
                })
    except Exception as e:
        logger.warning("Error fetching RSS feed %s: %s", feed_url, e)

    return articles


def fetch_italian_sources(company_name, keywords, config):
    """Fetch from Italian news source RSS feeds."""
    articles = []
    sources = config.get("sources", {})

    feed_sources = {
        "ansa": ("ANSA", "rss_url"),
        "sole24ore": ("Il Sole 24 Ore", "rss_url"),
        "reuters_it": ("Reuters Italia", "rss_url"),
    }

    for key, (name, url_field) in feed_sources.items():
        src = sources.get(key, {})
        if not src.get("enabled", True):
            continue
        feed_url = src.get(url_field)
        if feed_url:
            articles.extend(fetch_rss_feed(feed_url, name, company_name, keywords))

    return articles


def fetch_news_for_company(company_name, keywords, config):
    """Fetch news for a single company from all enabled sources."""
    max_articles = config.get("max_articles_per_company", 20)
    all_articles = []

    # Google News search (targeted per company)
    all_articles.extend(fetch_google_news(company_name, keywords, config))
    time.sleep(1)  # Rate limiting

    # Italian RSS sources (filtered by keywords)
    all_articles.extend(fetch_italian_sources(company_name, keywords, config))

    # Deduplicate by link
    seen_links = set()
    unique = []
    for article in all_articles:
        link = article["link"]
        if link and link not in seen_links:
            seen_links.add(link)
            unique.append(article)

    # Sort by date (newest first) and limit
    unique.sort(key=lambda a: a["published"], reverse=True)
    return unique[:max_articles]


def fetch_all_news(companies, config):
    """Fetch news for all companies. Returns a dict of company_name -> articles."""
    results = {}
    total = len(companies)

    for i, (name, keywords, sector) in enumerate(companies, 1):
        logger.info("Fetching news for %s (%d/%d)...", name, i, total)
        articles = fetch_news_for_company(name, keywords, config)
        if articles:
            results[name] = articles
            logger.info("  Found %d articles for %s", len(articles), name)
        else:
            logger.info("  No articles found for %s", name)

        # Rate limiting between companies
        if i < total:
            time.sleep(0.5)

    return results


# ---------------------------------------------------------------------------
# Italian macro economy & society news
# ---------------------------------------------------------------------------

MACRO_KEYWORDS = [
    "economia italiana",
    "PIL Italia",
    "inflazione Italia",
    "BCE tasso",
    "borsa italiana",
    "FTSE MIB",
    "spread BTP Bund",
    "debito pubblico Italia",
    "occupazione lavoro Italia",
    "governo italiano economia",
    "politica fiscale Italia",
    "export Made in Italy",
    "società italiana",
]


def fetch_macro_news(config):
    """
    Fetch general Italian economy & society news (not company-specific).

    Returns a list of article dicts.
    """
    max_articles = config.get("max_macro_articles", 30)
    source_cfg = config.get("sources", {}).get("google_news", {})
    if not source_cfg.get("enabled", True):
        return []

    base_url = source_cfg.get("base_url", "https://news.google.com/rss/search")
    lang = source_cfg.get("language", "it")
    country = source_cfg.get("country", "IT")

    all_articles = []
    for keyword in MACRO_KEYWORDS:
        query = urllib.parse.quote(keyword)
        url = f"{base_url}?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"
        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
            for entry in feed.entries:
                all_articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": _parse_date(entry),
                    "summary": _clean_html(entry.get("summary", "")),
                    "source": "Google News",
                })
        except Exception as e:
            logger.warning("Error fetching macro news for '%s': %s", keyword, e)
        time.sleep(0.5)

    # Also pull from Italian RSS feeds directly (economy sections)
    sources = config.get("sources", {})
    feed_sources = {
        "ansa": ("ANSA", "rss_url"),
        "sole24ore": ("Il Sole 24 Ore", "rss_url"),
    }
    for key, (name, url_field) in feed_sources.items():
        src = sources.get(key, {})
        if not src.get("enabled", True):
            continue
        feed_url = src.get(url_field)
        if not feed_url:
            continue
        try:
            feed = feedparser.parse(feed_url, agent=USER_AGENT)
            for entry in feed.entries:
                all_articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": _parse_date(entry),
                    "summary": _clean_html(entry.get("summary", "")),
                    "source": name,
                })
        except Exception as e:
            logger.warning("Error fetching macro RSS from %s: %s", name, e)

    # Deduplicate by link
    seen_links = set()
    unique = []
    for article in all_articles:
        link = article["link"]
        if link and link not in seen_links:
            seen_links.add(link)
            unique.append(article)

    unique.sort(key=lambda a: a["published"], reverse=True)
    logger.info("Fetched %d macro economy/society articles", len(unique[:max_articles]))
    return unique[:max_articles]
