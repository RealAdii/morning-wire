"""Generic RSS feed fetcher with dedup and time filtering."""

import hashlib
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser

import config

logger = logging.getLogger(__name__)


def fetch_feeds(feed_urls, max_age_hours=None):
    """Fetch articles from multiple RSS feeds, deduplicate, filter by age.

    Returns list of dicts: title, url, source, summary, published.
    """
    if max_age_hours is None:
        max_age_hours = config.ARTICLE_AGE_HOURS

    articles = []
    seen_urls = set()

    for feed_url in feed_urls:
        try:
            items = _fetch_single_feed(feed_url, max_age_hours)
            for item in items:
                url_key = _normalize_url(item["url"])
                if url_key not in seen_urls:
                    seen_urls.add(url_key)
                    articles.append(item)
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", feed_url, e)

    # Sort by published date descending
    articles.sort(key=lambda a: a.get("published", 0), reverse=True)
    return articles[:config.MAX_ARTICLES_PER_FEED]


def _fetch_single_feed(feed_url, max_age_hours):
    """Parse a single RSS feed and return normalized articles."""
    feed = feedparser.parse(feed_url)
    if feed.bozo and not feed.entries:
        logger.warning("Feed parse error for %s: %s", feed_url, feed.bozo_exception)
        return []

    source = _extract_source(feed, feed_url)
    cutoff = time.time() - (max_age_hours * 3600)
    articles = []

    for entry in feed.entries:
        published_ts = _get_timestamp(entry)
        if published_ts and published_ts < cutoff:
            continue

        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            continue

        summary = _extract_summary(entry)

        articles.append({
            "title": title,
            "url": url,
            "source": source,
            "summary": summary,
            "published": published_ts or time.time(),
        })

    return articles


def _extract_source(feed, feed_url):
    """Extract source name from feed metadata or URL."""
    if hasattr(feed, "feed") and hasattr(feed.feed, "title"):
        title = feed.feed.title
        if title:
            return title.split(" - ")[0].split(" | ")[0].strip()
    domain = urlparse(feed_url).netloc.replace("www.", "")
    return domain.split(".")[0].capitalize()


def _extract_summary(entry):
    """Extract clean summary text from feed entry."""
    summary = entry.get("summary", "") or entry.get("description", "")
    if not summary:
        content = entry.get("content", [])
        if content:
            summary = content[0].get("value", "")

    # Strip HTML tags (basic)
    if "<" in summary:
        from bs4 import BeautifulSoup
        summary = BeautifulSoup(summary, "html.parser").get_text()

    # Truncate
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return summary.strip()


def _get_timestamp(entry):
    """Extract published timestamp from feed entry."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return time.mktime(parsed)
            except (ValueError, OverflowError):
                pass
    return None


def _normalize_url(url):
    """Normalize URL for deduplication."""
    url = url.lower().rstrip("/")
    # Remove common tracking parameters
    if "?" in url:
        url = url.split("?")[0]
    return hashlib.md5(url.encode()).hexdigest()
