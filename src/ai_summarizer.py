"""
AI-powered summarizer using Claude API.

Generates narrative English summaries from Italian news articles.
Uses claude-haiku for cost efficiency (~$0.001 per summary call).
Falls back gracefully if ANTHROPIC_API_KEY is not set or API calls fail.
"""

import logging
import os

logger = logging.getLogger(__name__)

_client = None
_init_attempted = False

# Use Haiku for cost efficiency — fast and cheap for summarization
MODEL = "claude-haiku-4-5-20251001"


def _get_client():
    """Lazy-initialize the Anthropic client."""
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("ANTHROPIC_API_KEY not set; AI summaries disabled, using extractive fallback")
        return None

    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=api_key)
        logger.info("Claude API initialized for AI-powered summaries")
        return _client
    except ImportError:
        logger.warning("anthropic package not installed; AI summaries disabled")
        return None
    except Exception as e:
        logger.warning("Failed to initialize Claude API: %s", e)
        return None


def is_available():
    """Check if the AI summarizer is available."""
    return _get_client() is not None


def _build_articles_text(articles, max_articles=20):
    """Format articles into a text block for the prompt."""
    lines = []
    for i, article in enumerate(articles[:max_articles]):
        title = article.get("title", "")
        summary = article.get("summary", "")
        source = article.get("source", "Unknown")
        line = f"{i+1}. [{source}] {title}"
        if summary:
            line += f"\n   {summary[:200]}"
        lines.append(line)
    return "\n".join(lines)


def summarize_company_ai(company_name, articles):
    """
    Generate a narrative English summary for one company using Claude.

    Returns a summary string, or None if AI is unavailable/fails.
    """
    client = _get_client()
    if not client or not articles:
        return None

    articles_text = _build_articles_text(articles)
    n = len(articles)
    sources = sorted({a.get("source", "Unknown") for a in articles})

    prompt = f"""You are a financial news analyst. Below are {n} Italian news articles about {company_name} from today.

Articles:
{articles_text}

Write a concise English summary paragraph (3-5 sentences) that:
1. Captures the key developments and news themes
2. Mentions specific facts, numbers, or events when available
3. Uses a professional, analytical tone
4. Covers the most important stories first

Sources: {', '.join(sources)}

Write ONLY the summary paragraph, no headings or bullet points."""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.warning("Claude API call failed for %s: %s", company_name, e)
        return None


def summarize_macro_ai(macro_articles):
    """
    Generate a narrative English summary for Italian macro economy news using Claude.

    Returns a summary string, or None if AI is unavailable/fails.
    """
    client = _get_client()
    if not client or not macro_articles:
        return None

    articles_text = _build_articles_text(macro_articles, max_articles=25)
    n = len(macro_articles)
    sources = sorted({a.get("source", "Unknown") for a in macro_articles})

    prompt = f"""You are an economic analyst specializing in Italy. Below are {n} Italian news articles about Italy's economy and society from today.

Articles:
{articles_text}

Write a concise English briefing (4-6 sentences) that:
1. Highlights the most significant economic and political developments
2. Groups related stories into coherent themes
3. Mentions specific data points, policy decisions, or events when available
4. Uses a professional, analytical tone suitable for international investors

Sources: {', '.join(sources)}

Write ONLY the briefing paragraph, no headings or bullet points."""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.warning("Claude API call failed for macro summary: %s", e)
        return None


def translate_article_ai(title, summary=None):
    """
    Translate an Italian article title (and optionally summary) to English using Claude.

    Returns a dict with translated title and summary, or None if AI fails.
    """
    client = _get_client()
    if not client or not title:
        return None

    text_to_translate = f"Title: {title}"
    if summary:
        text_to_translate += f"\nSummary: {summary[:300]}"

    prompt = f"""Translate the following Italian news article text to English. Keep it natural and professional.

{text_to_translate}

Return ONLY the translated text in the same format (Title: ... and optionally Summary: ...)."""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        result = message.content[0].text.strip()
        translated = {}
        for line in result.split("\n"):
            if line.startswith("Title:"):
                translated["title"] = line[6:].strip()
            elif line.startswith("Summary:"):
                translated["summary"] = line[8:].strip()
        if "title" not in translated:
            translated["title"] = result.split("\n")[0].strip()
        return translated
    except Exception as e:
        logger.debug("Claude translation failed: %s", e)
        return None
