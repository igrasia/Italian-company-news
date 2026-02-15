"""
Summarizer module - generates English digests for each company's daily news,
and for Italian macro economy/society news.

When ANTHROPIC_API_KEY is set, uses Claude AI to produce narrative English
summaries. Otherwise, falls back to extractive summarization with optional
Google Translate for headline translation.
"""

import logging
import re

from src.ai_summarizer import is_available as ai_available
from src.ai_summarizer import summarize_company_ai, summarize_macro_ai
from src.translator import translate_batch

logger = logging.getLogger(__name__)


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

    Uses Claude AI for narrative summary when available, otherwise
    falls back to extractive summarization with translated headlines.

    Returns a dict with:
      - digest: str, a brief narrative paragraph or headline list
      - topic_count: int, number of distinct topics
      - sources: list[str], sources that covered this company
      - ai_generated: bool, whether AI was used
    """
    if not articles:
        return {"digest": "", "topic_count": 0, "sources": [], "ai_generated": False}

    titles = [a["title"] for a in articles if a.get("title")]
    sources = list({a.get("source", "Unknown") for a in articles})
    unique_titles = list(_deduplicate_phrases(titles))

    n = len(articles)
    src_text = ", ".join(sorted(sources))

    # Try AI summarization first
    if ai_available():
        ai_digest = summarize_company_ai(company_name, articles)
        if ai_digest:
            return {
                "digest": ai_digest,
                "topic_count": len(unique_titles),
                "sources": sorted(sources),
                "ai_generated": True,
            }

    # Fallback: extractive summarization with translated headlines
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
        "ai_generated": False,
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

    Uses Claude AI for narrative briefing when available, otherwise
    falls back to extractive summarization with translated headlines.

    Returns a dict with:
      - digest: str, narrative overview
      - topic_count: int
      - sources: list[str]
      - ai_generated: bool
    """
    if not macro_articles:
        return {
            "digest": "No Italian economy & society news found today.",
            "topic_count": 0,
            "sources": [],
            "ai_generated": False,
        }

    titles = [a["title"] for a in macro_articles if a.get("title")]
    sources = list({a.get("source", "Unknown") for a in macro_articles})
    unique_titles = list(_deduplicate_phrases(titles))

    # Try AI summarization first
    if ai_available():
        ai_digest = summarize_macro_ai(macro_articles)
        if ai_digest:
            return {
                "digest": ai_digest,
                "topic_count": len(unique_titles),
                "sources": sorted(sources),
                "ai_generated": True,
            }

    # Fallback: extractive summarization
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
        "ai_generated": False,
    }
