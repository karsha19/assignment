import re
from difflib import SequenceMatcher


def normalize_identifier(raw: str) -> str:
    """
    Normalization rule for entity identifiers (primarily vehicle numbers):
    - Uppercase
    - Strip whitespace
    - Remove non-alphanumeric characters
    This produces a canonical uppercase alphanumeric string used for exact
    comparisons. Fuzzy matching is performed elsewhere when enabled.
    """
    if raw is None:
        return ""
    cleaned = raw.strip().upper()
    # remove everything except A-Z0-9
    cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
    return cleaned


def similarity(a: str, b: str) -> float:
    """Return a 0..1 similarity ratio between two strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
