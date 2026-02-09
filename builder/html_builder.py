"""Jinja2 HTML builder for Morning Wire briefing."""

import logging
import os
import shutil
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)


def build_html(ai_signal, yc_companies, market_wire):
    """Render the briefing HTML and write to output directory.

    Returns path to generated index.html.
    """
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATE_DIR),
        autoescape=True,
    )
    template = env.get_template("index.html")

    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    html = template.render(
        date_str=date_str,
        timestamp=timestamp,
        ai_signal=ai_signal or [],
        yc_companies=yc_companies or [],
        market_wire=market_wire or [],
    )

    # Ensure output directory exists
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.ARCHIVE_DIR, exist_ok=True)

    # Write index.html
    output_path = os.path.join(config.OUTPUT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("Generated %s", output_path)

    # Archive a copy
    archive_name = now.strftime("%Y-%m-%d") + ".html"
    archive_path = os.path.join(config.ARCHIVE_DIR, archive_name)
    shutil.copy2(output_path, archive_path)
    logger.info("Archived to %s", archive_path)

    return output_path
