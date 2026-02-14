#!/usr/bin/env python3
"""
Italian Company News Search Application

Searches for daily news about major Italian companies from multiple sources
including Google News, ANSA, Il Sole 24 Ore, and Reuters Italia.

Usage:
    python main.py                  # Run once immediately
    python main.py --schedule       # Run on a daily schedule
    python main.py --list           # List tracked companies
    python main.py --stats          # Show database statistics
    python main.py --date 2025-01-15  # Show report for a specific date
    python main.py --sector Banking   # Search only Banking sector
"""

import argparse
import logging
import sys

import yaml

from src.companies import get_all_companies, get_companies_by_sector, get_sectors
from src.news_fetcher import fetch_all_news
from src.report import generate_reports
from src.scheduler import run_daily_job, start_scheduler
from src.storage import get_stats, get_today_articles, init_db, store_articles


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(config_path="config.yaml"):
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning("Config file %s not found, using defaults.", config_path)
        return {
            "schedule_time": "08:00",
            "max_articles_per_company": 20,
            "retention_days": 90,
            "sources": {
                "google_news": {
                    "enabled": True,
                    "base_url": "https://news.google.com/rss/search",
                    "language": "it",
                    "country": "IT",
                },
            },
            "output": {
                "console": True,
                "html": True,
                "json": True,
                "output_dir": "data",
            },
        }


def cmd_list_companies(args):
    """List all tracked companies."""
    companies = get_all_companies()
    sectors = get_sectors()

    print(f"\nTracked Italian Companies ({len(companies)} total)")
    print("=" * 60)

    for sector in sectors:
        sector_companies = get_companies_by_sector(sector)
        print(f"\n  {sector} ({len(sector_companies)})")
        for name, keywords, _ in sector_companies:
            kw = ", ".join(keywords)
            print(f"    - {name} [{kw}]")

    print()


def cmd_stats(args, config):
    """Show database statistics."""
    conn = init_db(config)
    try:
        stats = get_stats(conn)
        print("\nDatabase Statistics")
        print("=" * 40)
        print(f"  Total articles:       {stats['total_articles']}")
        print(f"  Companies with news:  {stats['companies_with_news']}")
        print(f"  Date range:           {stats['earliest_date']} to {stats['latest_date']}")

        if stats["top_companies"]:
            print("\n  Top companies by article count:")
            for company, count in stats["top_companies"]:
                print(f"    {company}: {count}")
        print()
    finally:
        conn.close()


def cmd_show_date(args, config):
    """Show articles for a specific date."""
    conn = init_db(config)
    try:
        articles = get_today_articles(conn, date=args.date)
        if not articles:
            print(f"\nNo articles found for {args.date}")
            return
        from src.report import print_console_report
        print_console_report(articles)
    finally:
        conn.close()


def cmd_run(args, config):
    """Run a single news search."""
    companies = get_all_companies()

    if args.sector:
        companies = get_companies_by_sector(args.sector)
        if not companies:
            print(f"No companies found in sector: {args.sector}")
            print(f"Available sectors: {', '.join(get_sectors())}")
            sys.exit(1)
        logging.info("Searching %d companies in sector: %s", len(companies), args.sector)

    if args.company:
        companies = [c for c in companies if args.company.lower() in c[0].lower()]
        if not companies:
            print(f"No company found matching: {args.company}")
            sys.exit(1)

    run_daily_job(config) if not (args.sector or args.company) else _run_filtered(companies, config)


def _run_filtered(companies, config):
    """Run search for a filtered set of companies."""
    conn = init_db(config)
    try:
        articles_by_company = fetch_all_news(companies, config)
        if articles_by_company:
            store_articles(conn, articles_by_company)
            generate_reports(articles_by_company, config)
        else:
            print("No articles found.")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Italian Company News Search - Daily news aggregator for major Italian companies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        Run search for all companies now
  python main.py --schedule             Start daily scheduler
  python main.py --list                 List tracked companies
  python main.py --sector Banking       Search Banking sector only
  python main.py --company Ferrari      Search a specific company
  python main.py --stats                Show database statistics
  python main.py --date 2025-01-15      Show report for a date
        """,
    )

    parser.add_argument("--schedule", action="store_true", help="Start the daily scheduler")
    parser.add_argument("--list", action="store_true", help="List all tracked companies")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--date", type=str, help="Show articles for a specific date (YYYY-MM-DD)")
    parser.add_argument("--sector", type=str, help="Filter by sector")
    parser.add_argument("--company", type=str, help="Filter by company name")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()
    setup_logging(args.verbose)
    config = load_config(args.config)

    if args.list:
        cmd_list_companies(args)
    elif args.stats:
        cmd_stats(args, config)
    elif args.date:
        cmd_show_date(args, config)
    elif args.schedule:
        start_scheduler(config)
    else:
        cmd_run(args, config)


if __name__ == "__main__":
    main()
