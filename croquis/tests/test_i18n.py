import re

from croquis.i18n import translate
from croquis.locales import ja


def test_translate_falls_back_to_english_key_for_unknown_language():
    assert translate("Options", "fr") == "Options"


def test_translate_falls_back_to_english_key_for_missing_translation():
    assert translate("Some string not in any catalog", "ja") == "Some string not in any catalog"


def test_translate_default_language_is_english():
    assert translate("Options") == "Options"


def test_translate_returns_japanese_when_available():
    assert translate("Options", "ja") == ja.TRANSLATIONS["Options"]


def test_translate_substitutes_kwargs():
    assert translate("Total: {total_time}", "en", total_time="5m") == "Total: 5m"
    assert translate("{n}s", "ja", n=30) == "30秒"


def test_ja_catalog_placeholders_match_english_keys():
    placeholder_re = re.compile(r"\{(\w+)\}")
    for key, value in ja.TRANSLATIONS.items():
        key_placeholders = set(placeholder_re.findall(key))
        value_placeholders = set(placeholder_re.findall(value))
        assert key_placeholders == value_placeholders, (
            f"placeholder mismatch for {key!r}: "
            f"key has {key_placeholders}, translation has {value_placeholders}"
        )
