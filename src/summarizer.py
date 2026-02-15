"""
Summarizer module - generates a brief English digest for each company's daily news,
and for Italian macro economy/society news.

Uses extractive summarization: picks key information from article titles
and summaries to create a concise overview paragraph.
Translates Italian headlines to English using Google Translate.
"""

import re

from src.translator import translate_batch


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


def _clean_title(title):
    """Strip trailing source attribution like ' - Reuters' from a title."""
    return re.sub(r"\s*[-–—|]\s*[A-Za-z .']+$", "", title).strip()


def summarize_company(company_name, articles):
    """
    Generate a short English digest for one company's articles.

    Returns a dict with:
      - digest: str, a brief narrative paragraph
      - topic_count: int, number of distinct topics
      - sources: list[str], sources that covered this company
    """
    if not articles:
        return {"digest": "", "topic_count": 0, "sources": []}

    titles = [a["title"] for a in articles if a.get("title")]
    sources = list({a.get("source", "Unknown") for a in articles})

    unique_titles = list(_deduplicate_phrases(titles))

    n = len(articles)
    src_text = ", ".join(sorted(sources))

    if n == 1:
        intro = f"{company_name} — 1 article from {src_text}."
    else:
        intro = f"{company_name} — {n} articles from {src_text}."

    # Up to 5 representative headlines, translated to English
    topic_lines = []
    for title in unique_titles[:5]:
        clean = _clean_title(title)
        if clean:
            topic_lines.append(clean)

    # Translate Italian headlines to English
    topic_lines = translate_batch(topic_lines)

    digest = intro
    if topic_lines:
        digest += "\n" + "\n".join(f"• {line}" for line in topic_lines)
    if len(unique_titles) > 5:
        remaining = len(unique_titles) - 5
        digest += f"\n  ...and {remaining} more."

    return {
        "digest": digest,
        "topic_count": len(unique_titles),
        "sources": sorted(sources),
    }


def summarize_all(articles_by_company):
    """
    Generate summaries for all companies.

    Returns a dict of company_name -> summary dict, sorted alphabetically.
    """
    summaries = {}
    for company in sorted(articles_by_company.keys()):
        articles = articles_by_company[company]
        summaries[company] = summarize_company(company, articles)
    return summaries


def summarize_macro(macro_articles):
    """
    Generate an English digest for Italian macro economy & society news.

    Returns a dict with:
      - digest: str, narrative overview
      - topic_count: int
      - sources: list[str]
      - articles: list[dict], the original articles for reference
    """
    if not macro_articles:
        return {
            "digest": "No Italian economy & society news found today.",
            "topic_count": 0,
            "sources": [],
        }

    titles = [a["title"] for a in macro_articles if a.get("title")]
    sources = list({a.get("source", "Unknown") for a in macro_articles})
    unique_titles = list(_deduplicate_phrases(titles))

    n = len(macro_articles)
    src_text = ", ".join(sorted(sources))
    intro = f"Today's Italian economy & society highlights — {n} articles from {src_text}."

    topic_lines = []
    for title in unique_titles[:8]:
        clean = _clean_title(title)
        if clean:
            topic_lines.append(clean)

    # Translate Italian headlines to English
    topic_lines = translate_batch(topic_lines)

    digest = intro
    if topic_lines:
        digest += "\n" + "\n".join(f"• {line}" for line in topic_lines)
    if len(unique_titles) > 8:
        remaining = len(unique_titles) - 8
        digest += f"\n  ...and {remaining} more."

    return {
        "digest": digest,
        "topic_count": len(unique_titles),
        "sources": sorted(sources),
    }
