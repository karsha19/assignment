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
    # Apply simple OCR post-corrections to fix common misreads such as
    # I <-> 1 and O <-> 0 before stripping punctuation. This increases
    # the chance an imperfect ANPR output still matches a watchlist entry.
    cleaned = _apply_ocr_post_corrections(cleaned)
    # remove everything except A-Z0-9
    cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
    return cleaned


def similarity(a: str, b: str) -> float:
    """Return a 0..1 similarity ratio between two strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _apply_ocr_post_corrections(raw: str) -> str:
    """Apply conservative OCR post-corrections to a raw identifier string.

    This uses a small, conservative mapping of commonly-confused characters
    and only runs simple replacements. It intentionally avoids aggressive
    transformations that could create false positives.
    """
    if not raw:
        return raw

    # If the string already looks clean (only alnum and reasonable length),
    # still attempt corrections because OCR often confuses characters.
    # Mapping focuses on characters that are visually similar:
    # I -> 1, L -> 1, O -> 0, Z -> 2, S -> 5, B -> 8, G -> 6
    mapping = {
        "I": "1",
        "L": "1",
        "O": "0",
        "Z": "2",
        "S": "5",
        "B": "8",
        "G": "6",
        "Q": "0",
    }

    # Only perform character substitutions when the string contains at least
    # one digit and one letter OR when it contains ambiguous letters/digits.
    has_digit = any(ch.isdigit() for ch in raw)
    has_alpha = any(ch.isalpha() for ch in raw)
    ambiguous = any(ch in mapping for ch in raw)

    if not ambiguous:
        return raw

    if not (has_digit and has_alpha) and not ambiguous:
        return raw

    # Build corrected candidate by replacing ambiguous chars using mapping.
    corrected = []
    for ch in raw:
        if ch in mapping:
            corrected.append(mapping[ch])
        else:
            corrected.append(ch)
    return "".join(corrected)
