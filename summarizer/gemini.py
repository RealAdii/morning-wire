"""Gemini REST API wrapper for generating summaries."""

import json
import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 15  # seconds


def call_gemini(prompt, max_tokens=2048):
    """Call Gemini REST API with retry on rate limits."""
    if not config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set")
        return None

    url = f"{config.GEMINI_URL}?key={config.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.3,
        },
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 429:
                delay = RETRY_BASE_DELAY * (attempt + 1)
                logger.warning("Rate limited, retrying in %ds (attempt %d/%d)", delay, attempt + 1, MAX_RETRIES)
                time.sleep(delay)
                continue
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (attempt + 1)
                logger.warning("Request failed, retrying in %ds: %s", delay, e)
                time.sleep(delay)
            else:
                logger.error("Gemini API request failed after %d retries: %s", MAX_RETRIES, e)
                return None
        except (KeyError, IndexError) as e:
            logger.error("Unexpected Gemini response structure: %s", e)
            return None

    return None


def summarize_ai_signal(articles):
    """Batch summarize AI articles into ranked signal items."""
    from summarizer.prompts import AI_SIGNAL_PROMPT

    if not articles:
        return []

    articles_text = "\n\n".join(
        f"[{i+1}] {a['title']}\nSource: {a.get('source', 'Unknown')}\n"
        f"URL: {a.get('url', '')}\n"
        f"Summary: {a.get('summary', 'No summary available.')}"
        for i, a in enumerate(articles[:15])
    )

    prompt = AI_SIGNAL_PROMPT.format(articles=articles_text, top_n=config.AI_SIGNAL_TOP_N)
    result = call_gemini(prompt, max_tokens=2048)
    if not result:
        return []

    return _parse_ranked_articles(result, articles)


def summarize_yc_company(company):
    """Generate an investor memo for a single YC company."""
    from summarizer.prompts import YC_MEMO_PROMPT

    company_text = (
        f"Company: {company.get('name', 'Unknown')}\n"
        f"Batch: {company.get('batch', 'Unknown')}\n"
        f"One-liner: {company.get('one_liner', 'N/A')}\n"
        f"Long description: {company.get('long_description', 'N/A')}\n"
        f"Tags: {', '.join(company.get('tags', []))}\n"
        f"URL: {company.get('url', 'N/A')}\n"
        f"Team size: {company.get('team_size', 'N/A')}\n"
        f"Location: {company.get('location', 'N/A')}\n"
        f"Status: {company.get('status', 'N/A')}"
    )

    prompt = YC_MEMO_PROMPT.format(company=company_text)
    result = call_gemini(prompt, max_tokens=512)
    if not result:
        return None

    return _parse_yc_memo(result, company)


def summarize_market_wire(articles):
    """Batch summarize market/fintech articles."""
    from summarizer.prompts import MARKET_WIRE_PROMPT

    if not articles:
        return []

    articles_text = "\n\n".join(
        f"[{i+1}] {a['title']}\nSource: {a.get('source', 'Unknown')}\n"
        f"URL: {a.get('url', '')}\n"
        f"Summary: {a.get('summary', 'No summary available.')}"
        for i, a in enumerate(articles[:15])
    )

    prompt = MARKET_WIRE_PROMPT.format(articles=articles_text, top_n=config.MARKET_WIRE_TOP_N)
    result = call_gemini(prompt, max_tokens=1536)
    if not result:
        return []

    return _parse_ranked_articles(result, articles)


def _parse_ranked_articles(text, original_articles):
    """Parse Gemini JSON response of ranked articles."""
    try:
        # Try to extract JSON from markdown code block
        if "```" in text:
            start = text.index("```") + 3
            if text[start:start+4] == "json":
                start += 4
            end = text.index("```", start)
            text = text[start:end].strip()
        items = json.loads(text)
        if not isinstance(items, list):
            items = items.get("articles", items.get("items", []))

        # Enrich with original URLs if missing
        url_map = {a["title"].lower().strip(): a for a in original_articles}
        for item in items:
            title_key = item.get("title", "").lower().strip()
            if title_key in url_map and not item.get("url"):
                item["url"] = url_map[title_key].get("url", "")
            if not item.get("source") and title_key in url_map:
                item["source"] = url_map[title_key].get("source", "")

        return items
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse Gemini ranked articles: %s", e)
        # Fallback: return original articles with basic formatting
        return [
            {
                "title": a["title"],
                "url": a.get("url", ""),
                "source": a.get("source", "Unknown"),
                "summary": a.get("summary", ""),
                "signal": "MEDIUM",
            }
            for a in original_articles[:7]
        ]


def _parse_yc_memo(text, company):
    """Parse Gemini JSON response for YC investor memo."""
    try:
        if "```" in text:
            start = text.index("```") + 3
            if text[start:start+4] == "json":
                start += 4
            end = text.index("```", start)
            text = text[start:end].strip()
        memo = json.loads(text)
        memo["name"] = company.get("name", "Unknown")
        memo["batch"] = company.get("batch", "")
        memo["url"] = company.get("url", "")
        memo["tags"] = company.get("tags", [])
        return memo
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse YC memo: %s", e)
        return {
            "name": company.get("name", "Unknown"),
            "batch": company.get("batch", ""),
            "url": company.get("url", ""),
            "tags": company.get("tags", []),
            "problem": company.get("one_liner", "N/A"),
            "solution": "See company website for details.",
            "market": "N/A",
            "why_now": "N/A",
            "signal": "MEDIUM",
        }
