#!/usr/bin/env python3
"""Morning Wire — Daily Investor Intelligence Briefing.

Pipeline: Fetch → Summarize → Build HTML → Deploy → Notify
"""

import logging
import os
import sys
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# --- Logging setup ---
os.makedirs(config.LOG_DIR, exist_ok=True)
log_file = os.path.join(config.LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("morning-wire")


def run():
    """Execute the full Morning Wire pipeline."""
    logger.info("=== Morning Wire pipeline starting ===")
    start = datetime.now()

    # ---- Phase 1: Fetch ----
    logger.info("Phase 1: Fetching data sources...")

    from fetchers.rss_fetcher import fetch_feeds
    from fetchers.hn_fetcher import fetch_hn_ai, fetch_hn_crypto
    from fetchers.yc_fetcher import fetch_yc_companies

    # Fetch RSS feeds
    ai_rss = fetch_feeds(config.AI_FEEDS)
    crypto_rss = fetch_feeds(config.CRYPTO_FEEDS)
    market_rss = fetch_feeds(config.MARKET_FEEDS)

    # Fetch HN stories
    hn_ai = fetch_hn_ai()
    hn_crypto = fetch_hn_crypto()

    # Combine AI articles (RSS + HN)
    ai_articles = ai_rss + hn_ai
    # Combine crypto into market (RSS + HN)
    crypto_articles = crypto_rss + hn_crypto
    market_articles = market_rss + crypto_articles

    # Fetch YC companies
    yc_companies_raw = fetch_yc_companies()

    logger.info(
        "Fetched: %d AI articles, %d market articles, %d YC companies",
        len(ai_articles), len(market_articles), len(yc_companies_raw),
    )

    # ---- Phase 2: Summarize ----
    logger.info("Phase 2: Generating Gemini summaries...")

    from summarizer.gemini import summarize_ai_signal, summarize_yc_company, summarize_market_wire

    import time as _time

    ai_signal = summarize_ai_signal(ai_articles)
    _time.sleep(5)  # pace API calls

    market_wire = summarize_market_wire(market_articles)
    _time.sleep(5)

    yc_memos = []
    for i, company in enumerate(yc_companies_raw):
        memo = summarize_yc_company(company)
        if memo:
            yc_memos.append(memo)
        if i < len(yc_companies_raw) - 1:
            _time.sleep(5)  # pace between YC calls

    logger.info(
        "Summarized: %d AI signals, %d YC memos, %d market items",
        len(ai_signal), len(yc_memos), len(market_wire),
    )

    # ---- Phase 3: Build HTML ----
    logger.info("Phase 3: Building HTML...")

    from builder.html_builder import build_html
    output_path = build_html(ai_signal, yc_memos, market_wire)
    logger.info("HTML generated: %s", output_path)

    # ---- Phase 4: Deploy ----
    logger.info("Phase 4: Deploying to GitHub Pages...")

    from deployer.github_pages import deploy
    deployed = deploy()
    if deployed:
        logger.info("Deployed to %s", config.GITHUB_PAGES_URL)
    else:
        logger.warning("Deployment skipped or failed")

    # ---- Phase 5: Notify ----
    logger.info("Phase 5: Sending notification...")

    from notifier.email_sender import send_notification
    stats = {
        "ai": len(ai_signal),
        "yc": len(yc_memos),
        "market": len(market_wire),
    }
    send_notification(success=True, stats=stats)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("=== Pipeline complete in %.1fs ===", elapsed)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        try:
            from notifier.email_sender import send_notification
            send_notification(success=False)
        except Exception:
            pass
        sys.exit(1)
