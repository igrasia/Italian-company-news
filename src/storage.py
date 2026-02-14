"""
SQLite storage module for persisting and deduplicating news articles.
"""

import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

DB_NAME = "italian_company_news.db"


def _get_db_path(config):
    output_dir = config.get("output", {}).get("output_dir", "data")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, DB_NAME)


def _article_hash(article):
    """Generate a unique hash for deduplication based on title and link."""
    key = f"{article['title']}|{article['link']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def init_db(config):
    """Initialize the SQLite database and create tables if needed."""
    db_path = _get_db_path(config)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            published TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            fetched_at TEXT NOT NULL,
            run_date TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_company ON articles(company)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_run_date ON articles(run_date)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_hash ON articles(hash)
    """)
    conn.commit()
    return conn


def store_articles(conn, articles_by_company):
    """Store articles, skipping duplicates. Returns count of new articles."""
    now = datetime.now(timezone.utc).isoformat()
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_count = 0

    for company, articles in articles_by_company.items():
        for article in articles:
            article_hash = _article_hash(article)
            try:
                conn.execute(
                    """INSERT INTO articles (hash, company, title, link, published, summary, source, fetched_at, run_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        article_hash,
                        company,
                        article["title"],
                        article["link"],
                        article["published"].isoformat(),
                        article.get("summary", ""),
                        article.get("source", ""),
                        now,
                        run_date,
                    ),
                )
                new_count += 1
            except sqlite3.IntegrityError:
                # Duplicate article, skip
                pass

    conn.commit()
    logger.info("Stored %d new articles", new_count)
    return new_count


def get_today_articles(conn, date=None):
    """Retrieve articles fetched today (or a specific date), grouped by company."""
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cursor = conn.execute(
        """SELECT company, title, link, published, summary, source
           FROM articles WHERE run_date = ? ORDER BY company, published DESC""",
        (date,),
    )
    rows = cursor.fetchall()

    result = {}
    for company, title, link, published, summary, source in rows:
        if company not in result:
            result[company] = []
        result[company].append({
            "title": title,
            "link": link,
            "published": published,
            "summary": summary,
            "source": source,
        })

    return result


def cleanup_old_articles(conn, retention_days):
    """Remove articles older than retention_days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).strftime(
        "%Y-%m-%d"
    )
    cursor = conn.execute("DELETE FROM articles WHERE run_date < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    if deleted:
        logger.info("Cleaned up %d old articles (older than %s)", deleted, cutoff)
    return deleted


def get_stats(conn):
    """Get database statistics."""
    stats = {}
    cursor = conn.execute("SELECT COUNT(*) FROM articles")
    stats["total_articles"] = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(DISTINCT company) FROM articles")
    stats["companies_with_news"] = cursor.fetchone()[0]

    cursor = conn.execute("SELECT MIN(run_date), MAX(run_date) FROM articles")
    row = cursor.fetchone()
    stats["earliest_date"] = row[0]
    stats["latest_date"] = row[1]

    cursor = conn.execute(
        "SELECT company, COUNT(*) as cnt FROM articles GROUP BY company ORDER BY cnt DESC LIMIT 10"
    )
    stats["top_companies"] = cursor.fetchall()

    return stats
