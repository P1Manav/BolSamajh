"""Text cleanup — filler removal, script control, formatting."""

import re
import logging
from typing import Literal

log = logging.getLogger(__name__)

# Common Hinglish fillers to remove
FILLERS_HI = [
    r"\b(umm?)\b", r"\b(uhh?)\b", r"\b(hmm+)\b", r"\b(aah+)\b",
    r"\b(toh)\b", r"\b(matlab)\b", r"\b(aur\s+haan)\b",
    r"\b(basically)\b", r"\b(actually)\b", r"\b(you\s*know)\b",
    r"\b(like)\b", r"\b(so)\b", r"\b(I\s*mean)\b",
    r"\b(woh\s+kya\s+hai)\b", r"\b(dekho)\b", r"\b(sun)\b",
    r"\b(haan\s+toh)\b", r"\b(accha)\b",
]

# Compiled filler patterns (case-insensitive)
_FILLER_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FILLERS_HI]

# Multiple spaces / leading/trailing cleanup
_MULTI_SPACE = re.compile(r"\s{2,}")


def remove_fillers(text: str) -> str:
    """Remove common speech fillers from Hinglish text."""
    result = text
    for pattern in _FILLER_PATTERNS:
        result = pattern.sub("", result)

    # Clean up resulting multiple spaces
    result = _MULTI_SPACE.sub(" ", result).strip()

    # Fix orphaned punctuation
    result = re.sub(r"\s+([,.\?!;:])", r"\1", result)

    if result != text:
        log.debug("Filler cleanup: %r → %r", text, result)
    return result


def apply_script_control(
    text: str,
    script: Literal["roman", "devanagari", "natural"] = "natural"
) -> str:
    """Apply script control to the transcribed text.

    - roman: transliterate any Devanagari to Roman script
    - devanagari: transliterate Roman Hindi words to Devanagari
    - natural: keep as-is (mixed script from STT output)
    """
    if script == "natural":
        return text

    if script == "roman":
        return _devanagari_to_roman(text)

    if script == "devanagari":
        # For devanagari mode, we keep English words as-is
        # and only convert romanized Hindi words
        return _roman_to_devanagari(text)

    return text


# Simple transliteration maps (covers common cases)
_DEVANAGARI_TO_ROMAN = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "अं": "an", "अः": "ah",
    "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha", "ङ": "nga",
    "च": "cha", "छ": "chha", "ज": "ja", "झ": "jha", "ञ": "nya",
    "ट": "ta", "ठ": "tha", "ड": "da", "ढ": "dha", "ण": "na",
    "त": "ta", "थ": "tha", "द": "da", "ध": "dha", "न": "na",
    "प": "pa", "फ": "pha", "ब": "ba", "भ": "bha", "म": "ma",
    "य": "ya", "र": "ra", "ल": "la", "व": "va", "श": "sha",
    "ष": "sha", "स": "sa", "ह": "ha",
    "ा": "a", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "n", "ः": "h", "्": "", "़": "",
    "।": ".", "॥": ".",
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}


def _devanagari_to_roman(text: str) -> str:
    """Convert Devanagari characters to approximate Roman script."""
    result = []
    for char in text:
        if char in _DEVANAGARI_TO_ROMAN:
            result.append(_DEVANAGARI_TO_ROMAN[char])
        else:
            result.append(char)
    return "".join(result)


def _roman_to_devanagari(text: str) -> str:
    """Convert romanized Hindi to Devanagari — keeps English words as-is.

    This is a simplified approach. For production use, consider
    a proper transliteration library like indic-transliteration.
    """
    # For now, keep as-is. Full transliteration requires more context.
    # The STT model already outputs Devanagari when language=hi,
    # so this is mainly a post-processing step.
    return text


def format_numbers(text: str) -> str:
    """Format numbers with Indian conventions (₹, lakhs, etc.)."""
    # Convert "rupees X" or "X rupees" to ₹X
    text = re.sub(
        r"(\d[\d,]*)\s*(?:rupees?|rupaye?|rs\.?)",
        r"₹\1",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?:rupees?|rupaye?|rs\.?)\s*(\d[\d,]*)",
        r"₹\1",
        text,
        flags=re.IGNORECASE,
    )
    return text


def cleanup_text(
    text: str,
    remove_filler: bool = True,
    script: Literal["roman", "devanagari", "natural"] = "natural",
) -> str:
    """Full text cleanup pipeline."""
    if not text:
        return text

    result = text.strip()

    if remove_filler:
        result = remove_fillers(result)

    result = format_numbers(result)
    result = apply_script_control(result, script)

    # Ensure first letter is capitalized for sentences
    if result and result[0].isalpha():
        result = result[0].upper() + result[1:]

    return result
