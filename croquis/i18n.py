from croquis.locales import ja

_CATALOGS = {"ja": ja.TRANSLATIONS}


def translate(key: str, language: str = "en", **kwargs) -> str:
    catalog = _CATALOGS.get(language, {})
    text = catalog.get(key, key)
    return text.format(**kwargs) if kwargs else text
