"""Y Combinator company fetcher with sector-based selection and rotation."""

import json
import logging
import os
import random
from datetime import datetime

import requests

import config

logger = logging.getLogger(__name__)


def fetch_yc_companies():
    """Fetch and select YC companies for today's briefing.

    Selects companies based on sector priority (AI > Crypto > Fintech),
    filters by recent batches, and rotates to avoid repeats.

    Returns list of company dicts.
    """
    try:
        resp = requests.get(config.YC_API_URL, timeout=30)
        resp.raise_for_status()
        all_companies = resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch YC companies: %s", e)
        return []

    # Filter to recent batches
    recent = [
        c for c in all_companies
        if c.get("batch") in config.YC_RECENT_BATCHES
        and c.get("status", "").lower() == "active"
    ]

    if not recent:
        # Fallback: any recent batch regardless of status
        recent = [c for c in all_companies if c.get("batch") in config.YC_RECENT_BATCHES]

    if not recent:
        logger.warning("No companies found in recent batches, using latest available")
        recent = sorted(all_companies, key=lambda c: c.get("batch", ""), reverse=True)[:200]

    # Load state to avoid re-featuring
    state = _load_state()
    featured_ids = set(state.get("featured_yc_ids", []))

    # Categorize by sector
    ai_companies = _filter_by_sector(recent, config.YC_AI_TAGS, featured_ids)
    crypto_companies = _filter_by_sector(recent, config.YC_CRYPTO_TAGS, featured_ids)
    fintech_companies = _filter_by_sector(recent, config.YC_FINTECH_TAGS, featured_ids)

    # Select based on priority
    selected = []
    ai_count = config.YC_SECTOR_PRIORITY.get("ai", 3)
    crypto_count = config.YC_SECTOR_PRIORITY.get("crypto", 1)
    fintech_count = config.YC_SECTOR_PRIORITY.get("fintech", 1)

    selected.extend(_pick_random(ai_companies, ai_count))
    selected.extend(_pick_random(crypto_companies, crypto_count))
    selected.extend(_pick_random(fintech_companies, fintech_count))

    # If we don't have enough, fill from any sector
    if len(selected) < config.YC_COMPANIES_PER_DAY:
        remaining = [
            c for c in recent
            if c.get("id") not in featured_ids
            and c.get("id") not in {s.get("id") for s in selected}
        ]
        needed = config.YC_COMPANIES_PER_DAY - len(selected)
        selected.extend(_pick_random(remaining, needed))

    # Update state
    new_ids = [c.get("id") for c in selected if c.get("id")]
    state["featured_yc_ids"] = list(featured_ids | set(new_ids))

    # Reset rotation if we've featured too many (cycle through)
    if len(state["featured_yc_ids"]) > 500:
        state["featured_yc_ids"] = new_ids

    _save_state(state)

    return selected[:config.YC_COMPANIES_PER_DAY]


def _filter_by_sector(companies, sector_tags, featured_ids):
    """Filter companies by sector tags, excluding already featured."""
    matches = []
    for c in companies:
        if c.get("id") in featured_ids:
            continue
        tags = [t.lower() for t in c.get("tags", [])]
        description = (c.get("one_liner", "") + " " + c.get("long_description", "")).lower()
        if any(tag in tags or tag in description for tag in sector_tags):
            matches.append(c)
    return matches


def _pick_random(companies, count):
    """Pick random companies from list."""
    if len(companies) <= count:
        return companies
    return random.sample(companies, count)


def _load_state():
    """Load state file."""
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"featured_yc_ids": [], "last_run": None, "run_count": 0}


def _save_state(state):
    """Save state file."""
    state["last_run"] = datetime.now().isoformat()
    state["run_count"] = state.get("run_count", 0) + 1
    try:
        with open(config.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        logger.error("Failed to save state: %s", e)
