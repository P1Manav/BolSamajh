"""Text cleanup — true disfluency removal, safe currency formatting, and offline transliteration script control.

Adheres strictly to Tier 5 Requirements:
- True disfluencies only (umm, uhh, hmm, aah, and Devanagari equivalents). Real words
  ('like', 'so', 'sun', 'actually', 'matlab', 'accha', 'dekho', 'toh') are preserved.
- Uses proper lookarounds instead of '\\b' for Devanagari characters:
  (?<![\\u0900-\\u097F\\w]) and (?![\\u0900-\\u097F\\w]).
- Word-boundary guarded currency regex: 'doctors 5' remains 'doctors 5', while
  'Rs 500', '500 rupees', 'rupaye 500' correctly format to '₹500'.
- Lakh and crore formatting: 'Rs 5 lakh', '5 lakh rupees', '2 crore rupees', '5 लाख रुपये' -> '₹5 lakh', '₹2 crore', '₹5 लाख'.
- Devanagari script control from Roman Hinglish marked as experimental (phonetic ITRANS).
"""

import re
import logging
from typing import Literal

from aksharamukha import transliterate

log = logging.getLogger(__name__)

# ONLY true speech disfluencies (vocal pauses/hesitations)
# Real semantic words ('like', 'so', 'actually', 'matlab', 'sun', 'dekho', 'toh', 'accha') are NEVER deleted.
TRUE_DISFLUENCIES = [
    # Roman / English disfluencies (use standard \b)
    r"\b(umm*)\b",
    r"\b(uhh*)\b",
    r"\b(hmmm*)\b",
    r"\b(aahh*)\b",
    r"\b(err*)\b",
    # Devanagari disfluencies — MUST use Unicode-aware lookarounds instead of \b
    r"(?<![\u0900-\u097F\w])(उम्म*)(?![\u0900-\u097F\w])",
    r"(?<![\u0900-\u097F\w])(उह+)(?![\u0900-\u097F\w])",
    r"(?<![\u0900-\u097F\w])(हम्म+)(?![\u0900-\u097F\w])",
    r"(?<![\u0900-\u097F\w])(आह+)(?![\u0900-\u097F\w])",
    r"(?<![\u0900-\u097F\w])(एर+)(?![\u0900-\u097F\w])",
]

_DISFLUENCY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in TRUE_DISFLUENCIES]
_MULTI_SPACE = re.compile(r"\s{2,}")


def remove_fillers(text: str) -> str:
    """Remove only true disfluencies (vocal hesitations like um, uh, hmm) from text."""
    if not text:
        return ""
    result = text
    for pattern in _DISFLUENCY_PATTERNS:
        result = pattern.sub("", result)

    # Clean up excess spaces created by removal
    result = _MULTI_SPACE.sub(" ", result).strip()

    # Fix punctuation that lost its preceding word
    result = re.sub(r"\s+([,.\?!;:])", r"\1", result)
    return result


def format_numbers(text: str) -> str:
    """Format currency and numbers with strict word-boundary checks and lakh/crore support.
    
    Prevents bugs like 'doctors 5' -> 'docto₹5'.
    Correctly converts:
    - 'Rs. 500', 'rupees 500', '500 rupees' -> '₹500'
    - 'Rs 5 lakh', '5 lakh rupees', '५ लाख रुपये' -> '₹5 lakh', '₹५ लाख'
    - 'Rs 2.5 crore', '2 crore rupees', '२ करोड़ रुपये' -> '₹2.5 crore', '₹२ करोड़'
    - '५०० रुपये', 'रु. 500' -> '₹५००', '₹500'
    """
    if not text:
        return ""

    # 1. Lakh and Crore currency patterns (e.g. 'Rs 5 lakh', '5 lakh rupees', 'Rs. 2.5 crore')
    # Prefix: Rs / rupees + number + lakh / crore
    text = re.sub(
        r"\b(?:rupees?|rupaye?|rs\.?)\s*(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)\b",
        r"₹\1 \2",
        text,
        flags=re.IGNORECASE,
    )
    # Suffix: number + lakh / crore + rupees / Rs
    text = re.sub(
        r"\b(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)\s*(?:rupees?|rupaye?|rs\.?)\b",
        r"₹\1 \2",
        text,
        flags=re.IGNORECASE,
    )

    # 2. Devanagari Lakh / Crore currency patterns using proper lookarounds
    text = re.sub(
        r"(?<![\u0900-\u097F\w])(?:रुपये|रुपए|रु\.?)\s*([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)\s*(लाख|करोड़)(?![\u0900-\u097F\w])",
        r"₹\1 \2",
        text,
    )
    text = re.sub(
        r"(?<![\u0900-\u097F\w])([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)\s*(लाख|करोड़)\s*(?:रुपये|रुपए|रु\.?)(?![\u0900-\u097F\w])",
        r"₹\1 \2",
        text,
    )

    # 3. Standard prefix currency: "\b(?:rupees?|rupaye?|rs\.?)\s*(\d...)"
    text = re.sub(
        r"\b(?:rupees?|rupaye?|rs\.?)\s*(\d[\d,]*(?:\.\d+)?)",
        r"₹\1",
        text,
        flags=re.IGNORECASE,
    )

    # 4. Standard suffix currency: "(\d...)\s*\b(?:rupees?|rupaye?|rs\.?)\b"
    text = re.sub(
        r"(\d[\d,]*(?:\.\d+)?)\s*\b(?:rupees?|rupaye?|rs\.?)\b",
        r"₹\1",
        text,
        flags=re.IGNORECASE,
    )

    # 5. Standard Devanagari currency: 'रुपये ५००', '५०० रुपये', 'रु. 500' using lookarounds
    text = re.sub(
        r"(?<![\u0900-\u097F\w])(?:रुपये|रुपए|रु\.?)\s*([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)(?![\u0900-\u097F\w])",
        r"₹\1",
        text,
    )
    text = re.sub(
        r"(?<![\u0900-\u097F\w])([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)\s*(?:रुपये|रुपए|रु\.?)(?![\u0900-\u097F\w])",
        r"₹\1",
        text,
    )

    return text


def apply_script_control(
    text: str,
    script: Literal["roman", "devanagari", "natural"] = "natural"
) -> str:
    """Apply verified offline script transliteration using Aksharamukha.
    
    - 'natural': keeps mixed script from STT output as-is (recommended for Hinglish).
    - 'roman': converts Devanagari/Gujarati script into phonetic Roman Latin script.
    - 'devanagari': [EXPERIMENTAL] converts Roman text into Devanagari via phonetic ITRANS.
      Note: English vocabulary (e.g. 'meeting') is not translated into Hindi, only
      phonetically transliterated.
    """
    if not text or script == "natural":
        return text

    if script == "roman":
        try:
            import unicodedata
            has_deva = bool(re.search(r"[\u0900-\u097f]", text))
            has_guj = bool(re.search(r"[\u0a80-\u0aff]", text))
            if has_deva:
                trans = transliterate.process("Devanagari", "ISO", text)
            elif has_guj:
                trans = transliterate.process("Gujarati", "ISO", text)
            else:
                trans = text
            # Strip diacritic accents for natural keyboard typing (e.g., bajē -> baje)
            decomposed = unicodedata.normalize("NFKD", trans)
            return "".join(c for c in decomposed if not unicodedata.combining(c))
        except Exception as e:
            log.warning("Roman transliteration failed: %s", e)
            return text

    if script == "devanagari":
        # EXPERIMENTAL: phonetic ITRANS transliteration
        try:
            has_roman = bool(re.search(r"[a-zA-Z]", text))
            if has_roman:
                log.debug("Applying experimental Roman->Devanagari ITRANS transliteration.")
                return transliterate.process("ITRANS", "Devanagari", text)
            return text
        except Exception as e:
            log.warning("Devanagari experimental transliteration failed: %s", e)
            return text

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

    # Capitalize first letter if alphabet
    if result and result[0].isalpha():
        result = result[0].upper() + result[1:]

    return result
