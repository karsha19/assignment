import re
from difflib import SequenceMatcher


def normalize_identifier(raw: str) -> str:
    if raw is None:
        return ""
    cleaned = raw.strip().upper()
    cleaned = _apply_ocr_post_corrections(cleaned)
    cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
    return cleaned


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _apply_ocr_post_corrections(raw: str) -> str:
    if not raw:
        return raw

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

    has_digit = any(ch.isdigit() for ch in raw)
    has_alpha = any(ch.isalpha() for ch in raw)
    ambiguous = any(ch in mapping for ch in raw)

    if not ambiguous:
        return raw

    if not (has_digit and has_alpha) and not ambiguous:
        return raw

    corrected = []
    for ch in raw:
        if ch in mapping:
            corrected.append(mapping[ch])
        else:
            corrected.append(ch)
    return "".join(corrected)
