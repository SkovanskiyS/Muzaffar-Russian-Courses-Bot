from pathlib import Path
import json
from typing import Literal, Dict, Set

LanguageCode = Literal["ru", "uz"]
DEFAULT_LANGUAGE: LanguageCode = "ru"

_translations: Dict[str, Dict[str, Dict[str, str]]] = {}

def load_translations():
    locales_dir = Path("locales")
    for lang_code in ["ru", "uz"]:
        lang_file = locales_dir / lang_code / "translations.json"
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                _translations[lang_code] = json.load(f)

def get_text(key: str, lang: LanguageCode = DEFAULT_LANGUAGE) -> str:
    """
    Get translated text for the given key in the specified language.
    Falls back to the key itself if translation is not found.
    """
    try:
        keys = key.split('.')
        value = _translations[lang]
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return key

def get_all_translations_for_key(key: str) -> Set[str]:
    """
    Get all possible translations for a given key across all languages.
    Useful for button text matching.
    """
    translations = set()
    for lang in ["ru", "uz"]:
        try:
            translations.add(get_text(key, lang))
        except (KeyError, TypeError):
            continue
    return translations

# Initialize translations
load_translations() 