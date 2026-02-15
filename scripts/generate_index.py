#!/usr/bin/env python3
"""Generate an index.html page listing all news reports for GitHub Pages."""

import glob
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "index.html")

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Italian Company News - Archive</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        header {{
            background: linear-gradient(135deg, #009246, #ffffff, #ce2b37);
            color: #333;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        header h1 {{ color: #1a1a1a; font-size: 2em; }}
        header p {{ color: #555; margin-top: 5px; }}
        .report-list {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .report-list h2 {{
            background: #009246;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
        }}
        .report-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .report-item:last-child {{ border-bottom: none; }}
        .report-item a {{
            color: #009246;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
        }}
        .report-item a:hover {{ text-decoration: underline; }}
        .report-item .links {{ display: flex; gap: 10px; }}
        .report-item .links a {{
            font-size: 0.85em;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: normal;
        }}
        .btn-html {{ background: #e8f5e9; color: #2e7d32 !important; }}
        .btn-json {{ background: #e3f2fd; color: #1565c0 !important; }}
        .empty {{
            padding: 40px 20px;
            text-align: center;
            color: #999;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Italian Company News</h1>
            <p>Daily news archive for major Italian companies</p>
        </header>

        <div class="report-list">
            <h2>Reports ({count} days)</h2>
            {items}
        </div>

        <footer>
            Powered by GitHub Actions &middot; Updated daily
        </footer>
    </div>
</body>
</html>"""


def extract_date(filename):
    """Extract date from filename like news_report_2025-01-15.html."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None


def generate_index():
    html_files = sorted(glob.glob(os.path.join(DATA_DIR, "news_report_*.html")), reverse=True)

    if not html_files:
        items = '<div class="empty">No reports yet. The first report will appear after the next scheduled run.</div>'
        count = 0
    else:
        item_parts = []
        for filepath in html_files:
            filename = os.path.basename(filepath)
            date = extract_date(filename) or filename
            json_filename = filename.replace(".html", ".json")
            json_path = os.path.join(DATA_DIR, json_filename)

            links = f'<a class="btn-html" href="{filename}">HTML</a>'
            if os.path.exists(json_path):
                links += f' <a class="btn-json" href="{json_filename}">JSON</a>'

            item_parts.append(
                f'<div class="report-item">'
                f'<a href="{filename}">{date}</a>'
                f'<div class="links">{links}</div>'
                f'</div>'
            )
        items = "\n            ".join(item_parts)
        count = len(html_files)

    html = INDEX_TEMPLATE.format(count=count, items=items)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Index page generated: {OUTPUT_PATH} ({count} reports)")


if __name__ == "__main__":
    generate_index()
