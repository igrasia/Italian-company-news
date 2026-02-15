"""
Summarizer module - generates a brief digest for each company's daily news.

Uses extractive summarization: picks key information from article titles
and summaries to create a concise overview paragraph per company.
"""

import re
from collections import Counter


def _deduplicate_phrases(titles):
    """Remove near-duplicate titles (e.g. same story from different sources)."""
    seen = []
    for t in titles:
        normalized = re.sub(r"\s+", " ", t.lower().strip())
        # skip if >60% overlap with something already seen
        is_dup = False
        for s in seen:
            common = set(normalized.split()) & set(s.split())
            shorter = min(len(normalized.split()), len(s.split()))
            if shorter > 0 and len(common) / shorter > 0.6:
                is_dup = True
                break
        if not is_dup:
            seen.append(normalized)
            yield t


def summarize_company(company_name, articles):
    """
    Generate a short Italian-language digest for one company's articles.

    Returns a dict with:
      - digest: str, a brief narrative paragraph
      - topic_count: int, number of distinct topics
      - sources: list[str], sources that covered this company
    """
    if not articles:
        return {"digest": "", "topic_count": 0, "sources": []}

    titles = [a["title"] for a in articles if a.get("title")]
    sources = list({a.get("source", "Sconosciuto") for a in articles})

    # Pick distinct headlines as topic bullets
    unique_titles = list(_deduplicate_phrases(titles))

    # Build digest: short narrative + bullet points of key headlines
    n = len(articles)
    src_text = ", ".join(sorted(sources))

    if n == 1:
        intro = f"{company_name} — 1 notizia da {src_text}."
    else:
        intro = f"{company_name} — {n} notizie da {src_text}."

    # Take up to 5 most representative headlines as topic points
    topic_lines = []
    for title in unique_titles[:5]:
        # Clean trailing source attribution like " - Reuters"
        clean = re.sub(r"\s*[-–—|]\s*[A-Za-z .']+$", "", title).strip()
        if clean:
            topic_lines.append(clean)

    digest = intro
    if topic_lines:
        digest += "\n" + "\n".join(f"• {line}" for line in topic_lines)
    if len(unique_titles) > 5:
        remaining = len(unique_titles) - 5
        digest += f"\n  ...e altre {remaining} notizie."

    return {
        "digest": digest,
        "topic_count": len(unique_titles),
        "sources": sorted(sources),
    }


def summarize_all(articles_by_company):
    """
    Generate summaries for all companies.

    Returns a dict of company_name -> summary dict.
    Companies are sorted alphabetically.
    """
    summaries = {}
    for company in sorted(articles_by_company.keys()):
        articles = articles_by_company[company]
        summaries[company] = summarize_company(company, articles)
    return summaries
