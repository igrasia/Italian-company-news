"""
Report generation module - creates console, HTML, and JSON reports.
"""

import json
import logging
import os
from datetime import datetime, timezone

from jinja2 import Template

from src.summarizer import summarize_all

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Italian Company News - {{ date }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #009246, #ffffff, #ce2b37);
            color: #333;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        header h1 { color: #1a1a1a; font-size: 2em; }
        header p { color: #555; margin-top: 5px; }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 200px;
            text-align: center;
        }
        .stat-card h3 { color: #009246; font-size: 2em; }
        .stat-card p { color: #666; }

        /* Daily digest section */
        .digest-section {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow: hidden;
        }
        .digest-title {
            background: #1a1a1a;
            color: white;
            padding: 15px 20px;
            font-size: 1.3em;
        }
        .digest-company {
            padding: 18px 20px;
            border-bottom: 1px solid #eee;
        }
        .digest-company:last-child { border-bottom: none; }
        .digest-company h3 {
            color: #009246;
            font-size: 1.1em;
            margin-bottom: 6px;
            cursor: pointer;
        }
        .digest-company h3 .toggle { font-size: 0.8em; color: #aaa; margin-left: 6px; }
        .digest-meta {
            font-size: 0.82em;
            color: #999;
            margin-bottom: 8px;
        }
        .digest-text {
            color: #444;
            font-size: 0.95em;
            white-space: pre-line;
        }

        /* Collapsible article details */
        .company-section {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }
        .company-header {
            background: #009246;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        .company-header .count {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        .article {
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
        }
        .article:last-child { border-bottom: none; }
        .article h3 { margin-bottom: 5px; }
        .article h3 a {
            color: #1a1a1a;
            text-decoration: none;
        }
        .article h3 a:hover { color: #009246; }
        .article .meta {
            font-size: 0.85em;
            color: #888;
            margin-bottom: 8px;
        }
        .article .meta span { margin-right: 15px; }
        .article .summary { color: #555; font-size: 0.95em; }
        footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Italian Company News</h1>
            <p>Daily news digest - {{ date }}</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <h3>{{ total_articles }}</h3>
                <p>Total Articles</p>
            </div>
            <div class="stat-card">
                <h3>{{ total_companies }}</h3>
                <p>Companies Covered</p>
            </div>
            <div class="stat-card">
                <h3>{{ total_sources }}</h3>
                <p>News Sources</p>
            </div>
        </div>

        <!-- Daily Digest -->
        <div class="digest-section">
            <div class="digest-title">Riepilogo del giorno</div>
            {% for company, summary in summaries.items() %}
            <div class="digest-company">
                <h3>{{ company }} <span class="toggle">[{{ summary.topic_count }} topics]</span></h3>
                <div class="digest-meta">Fonti: {{ summary.sources | join(', ') }}</div>
                <div class="digest-text">{{ summary.digest }}</div>
            </div>
            {% endfor %}
        </div>

        <!-- Full Article List per Company -->
        {% for company, articles in articles_by_company.items() %}
        <div class="company-section">
            <div class="company-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                {{ company }}
                <span class="count">{{ articles|length }} articles — click to expand</span>
            </div>
            <div style="display:none">
            {% for article in articles %}
            <div class="article">
                <h3><a href="{{ article.link }}" target="_blank">{{ article.title }}</a></h3>
                <div class="meta">
                    <span>{{ article.source }}</span>
                    <span>{{ article.published }}</span>
                </div>
                {% if article.summary %}
                <p class="summary">{{ article.summary[:300] }}{% if article.summary|length > 300 %}...{% endif %}</p>
                {% endif %}
            </div>
            {% endfor %}
            </div>
        </div>
        {% endfor %}

        <footer>
            Generated by Italian Company News Search App
        </footer>
    </div>
</body>
</html>"""


def print_console_report(articles_by_company):
    """Print a formatted report to the console."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = sum(len(a) for a in articles_by_company.values())
    summaries = summarize_all(articles_by_company)

    print("\n" + "=" * 70)
    print(f"  ITALIAN COMPANY NEWS REPORT - {date_str}")
    print(f"  {len(articles_by_company)} companies | {total} articles")
    print("=" * 70)

    # Print digest first
    print("\n  RIEPILOGO DEL GIORNO")
    print("-" * 70)
    for company, summary in summaries.items():
        print(f"\n  {summary['digest']}")
    print("\n" + "-" * 70)

    # Then full article listing
    for company, articles in sorted(articles_by_company.items()):
        print(f"\n--- {company} ({len(articles)} articles) ---")
        for article in articles:
            pub = article["published"]
            if hasattr(pub, "strftime"):
                pub = pub.strftime("%Y-%m-%d %H:%M")
            print(f"  [{article['source']}] {article['title']}")
            print(f"    {pub} | {article['link']}")
            if article.get("summary"):
                summary = article["summary"][:150]
                if len(article["summary"]) > 150:
                    summary += "..."
                print(f"    {summary}")
            print()

    print("=" * 70)
    print()


def generate_html_report(articles_by_company, output_dir):
    """Generate an HTML report."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_articles = sum(len(a) for a in articles_by_company.values())
    sources = set()
    for articles in articles_by_company.values():
        for a in articles:
            sources.add(a.get("source", "Unknown"))

    summaries = summarize_all(articles_by_company)

    # Convert datetime objects to strings for the template
    template_data = {}
    for company in sorted(articles_by_company.keys()):
        articles = articles_by_company[company]
        template_data[company] = []
        for article in articles:
            a = dict(article)
            if hasattr(a["published"], "strftime"):
                a["published"] = a["published"].strftime("%Y-%m-%d %H:%M")
            template_data[company].append(a)

    template = Template(HTML_TEMPLATE)
    html = template.render(
        date=date_str,
        total_articles=total_articles,
        total_companies=len(articles_by_company),
        total_sources=len(sources),
        summaries=summaries,
        articles_by_company=template_data,
    )

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"news_report_{date_str}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("HTML report saved to %s", filepath)
    return filepath


def generate_json_report(articles_by_company, output_dir):
    """Generate a JSON report."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summaries = summarize_all(articles_by_company)

    output = {
        "date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": sum(len(a) for a in articles_by_company.values()),
        "total_companies": len(articles_by_company),
        "summaries": summaries,
        "companies": {},
    }

    for company in sorted(articles_by_company.keys()):
        articles = articles_by_company[company]
        output["companies"][company] = []
        for article in articles:
            a = dict(article)
            if hasattr(a["published"], "strftime"):
                a["published"] = a["published"].isoformat()
            output["companies"][company].append(a)

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"news_report_{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("JSON report saved to %s", filepath)
    return filepath


def generate_reports(articles_by_company, config):
    """Generate all configured report types."""
    output_cfg = config.get("output", {})
    output_dir = output_cfg.get("output_dir", "data")
    reports = []

    if output_cfg.get("console", True):
        print_console_report(articles_by_company)

    if output_cfg.get("html", True):
        path = generate_html_report(articles_by_company, output_dir)
        reports.append(path)

    if output_cfg.get("json", True):
        path = generate_json_report(articles_by_company, output_dir)
        reports.append(path)

    return reports
