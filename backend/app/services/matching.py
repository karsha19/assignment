import re


def normalize_identifier(raw: str) -> str:
    """
    Documented normalization rule for entity identifiers (primarily vehicle numbers):
    - Uppercase
    - Strip all whitespace
    - Remove hyphens and dots
    This is an exact-match normalization. No fuzzy/partial matching is performed,
    to avoid false-positive watchlist matches.
    """
    if raw is None:
        return ""
    cleaned = raw.strip().upper()
    cleaned = re.sub(r"[\s\-\.]", "", cleaned)
    return cleaned
