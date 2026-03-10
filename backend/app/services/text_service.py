"""
Text translation service using deep-translator (Google Translate) 
and optional Gemini API for higher quality novel translation.
"""

from deep_translator import GoogleTranslator
from cachetools import TTLCache
import os

# Cache translations for 1 hour, max 1000 entries
_translation_cache = TTLCache(maxsize=1000, ttl=3600)

# Supported languages
SUPPORTED_LANGUAGES = {
    "vi": "vietnamese",
    "en": "english",
    "zh-CN": "chinese (simplified)",
    "zh-TW": "chinese (traditional)",
    "ja": "japanese",
    "ko": "korean",
    "th": "thai",
    "fr": "french",
    "de": "german",
    "es": "spanish",
    "ru": "russian",
    "pt": "portuguese",
    "id": "indonesian",
    "auto": "auto",
}


def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "vi",
    use_gemini: bool = False,
    gemini_api_key: str | None = None,
) -> str:
    """Translate text using Google Translate or Gemini API."""
    if not text or not text.strip():
        return ""

    # Check cache
    cache_key = f"{source_lang}:{target_lang}:{text[:200]}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    if use_gemini and gemini_api_key:
        result = _translate_with_gemini(text, source_lang, target_lang, gemini_api_key)
    else:
        result = _translate_with_google(text, source_lang, target_lang)

    # Store in cache
    _translation_cache[cache_key] = result
    return result


def _translate_with_google(text: str, source_lang: str, target_lang: str) -> str:
    """Free translation using Google Translate via deep-translator."""
    try:
        # deep-translator handles chunking for long texts
        translator = GoogleTranslator(source=source_lang, target=target_lang)

        # Split long text into chunks (deep-translator has a 5000 char limit)
        max_chunk = 4500
        if len(text) <= max_chunk:
            return translator.translate(text)

        # Split by paragraphs for better context
        paragraphs = text.split("\n")
        translated_parts = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 <= max_chunk:
                current_chunk += para + "\n"
            else:
                if current_chunk.strip():
                    translated_parts.append(translator.translate(current_chunk.strip()))
                current_chunk = para + "\n"

        if current_chunk.strip():
            translated_parts.append(translator.translate(current_chunk.strip()))

        return "\n".join(translated_parts)

    except Exception as e:
        raise Exception(f"Google Translate error: {str(e)}")


def _translate_with_gemini(
    text: str, source_lang: str, target_lang: str, api_key: str
) -> str:
    """Higher quality translation using Gemini API (free tier)."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        source_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
        target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)

        prompt = f"""You are a professional novel translator. Translate the following text from {source_name} to {target_name}.
        
Rules:
- Maintain the original meaning, tone, and style
- Keep names and proper nouns consistent
- Preserve paragraph formatting
- Translate naturally, not word-by-word
- Do NOT add any commentary, only output the translated text

Text to translate:
{text}"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        # Fallback to Google Translate
        print(f"Gemini API error: {str(e)}, falling back to Google Translate")
        return _translate_with_google(text, source_lang, target_lang)


def get_supported_languages() -> dict:
    """Return the list of supported languages."""
    return SUPPORTED_LANGUAGES
