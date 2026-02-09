"""Gmail SMTP notification sender."""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def send_notification(success=True, stats=None):
    """Send email notification with link to today's briefing.

    Args:
        success: Whether the pipeline completed successfully.
        stats: Dict with article counts, e.g. {"ai": 7, "yc": 5, "market": 5}.
    """
    if not all([config.EMAIL_FROM, config.EMAIL_TO, config.EMAIL_APP_PASSWORD]):
        logger.warning("Email not configured — skipping notification")
        return False

    stats = stats or {}
    date_str = datetime.now().strftime("%B %d, %Y")

    if success:
        subject = f"Morning Wire — {date_str}"
        body = _build_success_body(date_str, stats)
    else:
        subject = f"Morning Wire FAILED — {date_str}"
        body = _build_failure_body(date_str)

    msg = MIMEMultipart("alternative")
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO
    msg["Subject"] = subject

    # Plain text version
    msg.attach(MIMEText(body["text"], "plain"))
    # HTML version
    msg.attach(MIMEText(body["html"], "html"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.EMAIL_FROM, config.EMAIL_APP_PASSWORD)
            server.sendmail(config.EMAIL_FROM, config.EMAIL_TO, msg.as_string())
        logger.info("Notification email sent to %s", config.EMAIL_TO)
        return True
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return False


def _build_success_body(date_str, stats):
    """Build success notification body."""
    ai_count = stats.get("ai", 0)
    yc_count = stats.get("yc", 0)
    market_count = stats.get("market", 0)

    text = (
        f"Morning Wire — {date_str}\n\n"
        f"Today's briefing is live: {config.GITHUB_PAGES_URL}\n\n"
        f"AI Signal: {ai_count} stories\n"
        f"YC Deal Flow: {yc_count} companies\n"
        f"Market Wire: {market_count} stories\n"
    )

    html = f"""
    <div style="font-family: Verdana, sans-serif; max-width: 500px;">
        <div style="background: #ff6600; padding: 8px 16px;">
            <span style="font-weight: bold; font-size: 14px;">&#x26A1; Morning Wire</span>
            <span style="float: right; font-size: 11px; opacity: 0.8;">{date_str}</span>
        </div>
        <div style="padding: 16px; background: #f6f6ef;">
            <p style="margin: 0 0 12px;">
                <a href="{config.GITHUB_PAGES_URL}" style="color: #ff6600; font-weight: bold; font-size: 13px;">
                    Read today's briefing &rarr;
                </a>
            </p>
            <table style="font-size: 11px; color: #666;">
                <tr><td style="padding: 2px 8px 2px 0;">AI Signal</td><td><b>{ai_count}</b> stories</td></tr>
                <tr><td style="padding: 2px 8px 2px 0;">YC Deal Flow</td><td><b>{yc_count}</b> companies</td></tr>
                <tr><td style="padding: 2px 8px 2px 0;">Market Wire</td><td><b>{market_count}</b> stories</td></tr>
            </table>
        </div>
    </div>
    """

    return {"text": text, "html": html}


def _build_failure_body(date_str):
    """Build failure notification body."""
    text = (
        f"Morning Wire — {date_str}\n\n"
        f"Pipeline failed. Check logs at ~/morning-wire/logs/\n"
    )
    html = f"""
    <div style="font-family: Verdana, sans-serif; max-width: 500px;">
        <div style="background: #cc0000; padding: 8px 16px; color: #fff;">
            <span style="font-weight: bold;">Morning Wire — FAILED</span>
        </div>
        <div style="padding: 16px;">
            <p>Pipeline failed on {date_str}. Check logs at <code>~/morning-wire/logs/</code></p>
        </div>
    </div>
    """
    return {"text": text, "html": html}
