"""Hacker News API fetcher with keyword filtering and point thresholds."""

import logging
import time

import requests

import config

logger = logging.getLogger(__name__)


def fetch_hn_stories(keywords, min_points=50, max_stories=15):
    """Fetch top HN stories matching keywords above point threshold.

    Returns list of dicts: title, url, source, summary, published, points.
    """
    try:
        resp = requests.get(config.HN_TOP_URL, timeout=15)
        resp.raise_for_status()
        story_ids = resp.json()[:200]  # Check top 200
    except requests.RequestException as e:
        logger.error("Failed to fetch HN top stories: %s", e)
        return []

    matched = []
    for story_id in story_ids:
        if len(matched) >= max_stories:
            break

        story = _fetch_story(story_id)
        if not story:
            continue

        points = story.get("score", 0)
        if points < min_points:
            continue

        title = story.get("title", "").lower()
        if not any(kw in title for kw in keywords):
            continue

        url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
        matched.append({
            "title": story.get("title", ""),
            "url": url,
            "source": f"HN ({points} pts)",
            "summary": f"Hacker News discussion with {story.get('descendants', 0)} comments.",
            "published": story.get("time", time.time()),
            "points": points,
        })

    matched.sort(key=lambda s: s["points"], reverse=True)
    return matched


def fetch_hn_ai():
    """Fetch AI-related HN stories."""
    return fetch_hn_stories(config.AI_KEYWORDS, min_points=config.HN_AI_MIN_POINTS)


def fetch_hn_crypto():
    """Fetch crypto-related HN stories."""
    return fetch_hn_stories(config.CRYPTO_KEYWORDS, min_points=config.HN_CRYPTO_MIN_POINTS)


def _fetch_story(story_id):
    """Fetch a single HN story by ID."""
    try:
        url = config.HN_ITEM_URL.format(story_id)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None
