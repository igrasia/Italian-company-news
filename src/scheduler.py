"""
Scheduler module - runs the news search on a daily schedule.
"""

import logging
import signal
import sys

import schedule

from src.companies import get_all_companies
from src.news_fetcher import fetch_all_news
from src.report import generate_reports
from src.storage import cleanup_old_articles, init_db, store_articles

logger = logging.getLogger(__name__)


def run_daily_job(config):
    """Execute a single news search run."""
    logger.info("=" * 60)
    logger.info("Starting daily Italian company news search...")
    logger.info("=" * 60)

    companies = get_all_companies()
    conn = init_db(config)

    try:
        # Fetch news
        articles_by_company = fetch_all_news(companies, config)

        if not articles_by_company:
            logger.warning("No articles found in this run.")
            return

        # Store in database
        new_count = store_articles(conn, articles_by_company)
        logger.info("Total new articles stored: %d", new_count)

        # Generate reports
        generate_reports(articles_by_company, config)

        # Cleanup old articles
        retention = config.get("retention_days", 90)
        cleanup_old_articles(conn, retention)

        total_articles = sum(len(a) for a in articles_by_company.values())
        companies_found = len(articles_by_company)
        logger.info(
            "Run complete: %d articles for %d companies (%d new)",
            total_articles,
            companies_found,
            new_count,
        )
    finally:
        conn.close()


def start_scheduler(config):
    """Start the daily scheduler."""
    schedule_time = config.get("schedule_time", "08:00")

    logger.info("Scheduling daily news search at %s", schedule_time)
    schedule.every().day.at(schedule_time).do(run_daily_job, config=config)

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down scheduler...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    logger.info("Next run scheduled at %s", schedule_time)

    while True:
        schedule.run_pending()
        import time
        time.sleep(60)
