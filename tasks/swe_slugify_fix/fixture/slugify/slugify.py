import re

TRANSLIT = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "ё": "yo",
}

def slugify(value: str) -> str:
    """Return a hyphen separated identifier for the given value."""

    if not isinstance(value, str):
        raise TypeError("value must be a string")

    text = value.lower()
    for char, repl in TRANSLIT.items():
        text = text.replace(char, repl)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text
