"""
Translator module - translates Italian text to English.

Uses deep-translator with multiple backends (Google Translate, MyMemory).
Falls back gracefully to original text if all translation services fail.
"""

import logging
import time

logger = logging.getLogger(__name__)

_translator = None
_init_attempted = False


def _get_translator():
    """Lazy-initialize the translator, trying multiple backends."""
    global _translator, _init_attempted
    if _init_attempted:
        return _translator
    _init_attempted = True

    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="it", target="en")
        # Test with a short phrase to verify connectivity
        t.translate("test")
        _translator = t
        logger.info("Using Google Translate backend")
        return _translator
    except Exception:
        pass

    try:
        from deep_translator import MyMemoryTranslator
        t = MyMemoryTranslator(source="it-IT", target="en-GB")
        t.translate("test")
        _translator = t
        logger.info("Using MyMemory Translate backend")
        return _translator
    except Exception:
        pass

    logger.warning("No translation service available; articles will remain in Italian")
    _translator = None
    return None


def translate_text(text, max_retries=2):
    """
    Translate a single Italian text string to English.

    Returns the English translation, or the original text if translation fails.
    """
    if not text or not text.strip():
        return text

    translator = _get_translator()
    if translator is None:
        return text

    for attempt in range(max_retries + 1):
        try:
            result = translator.translate(text.strip())
            return result if result else text
        except Exception as e:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
            else:
                logger.debug("Translation failed for '%.50s...': %s", text, e)
                return text


def translate_batch(texts, max_retries=2):
    """
    Translate a list of Italian texts to English.

    Returns a list of English translations (same length as input).
    Falls back to original text for any item that fails.
    """
    if not texts:
        return []

    translator = _get_translator()
    if translator is None:
        return list(texts)

    results = []
    for i, text in enumerate(texts):
        translated = translate_text(text, max_retries=max_retries)
        results.append(translated)
        # Small delay between requests to avoid rate limiting
        if i < len(texts) - 1:
            time.sleep(0.1)

    return results
