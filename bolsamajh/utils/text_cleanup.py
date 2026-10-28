r"""Text cleanup — true disfluency removal, currency, percentage, and phone formatting, plus offline transliteration.

Adheres strictly to Tier 5 Requirements:
- True disfluencies only (umm, uhh, hmm, aah, and Devanagari equivalents). Real semantic words
  ('like', 'so', 'actually', 'matlab', 'sun', 'dekho', 'toh', 'accha') are preserved.
- Unicode-aware lookarounds for Devanagari: (?<![\u0900-\u097F\w]) and (?![\u0900-\u097F\w]).
- Word-boundary guarded currency regex: 'doctors 5' remains 'doctors 5', while
  'Rs 500', '500 rupees', 'rupaye 500', '500 rupaya' correctly format to '₹500'.
- Percent normalization: '50 percent', '50 per cent', '50 प्रतिशत', '५० प्रतिशत' -> '50%', '५०%'.
- Phone number normalization: 10-digit mobile numbers formatted as 5-5 digit blocks (e.g. 98765 43210).
- Lakh and crore formatting: 'Rs 5 lakh', '5 lakh rupees', '2 crore rupees', '5 लाख रुपये' -> '₹5 lakh', '₹2 crore', '₹5 लाख'.
- Roman mode with lazy Aksharamukha and anusvara -> 'n' fix (never produces 'himdi' for 'hindi').
"""

import logging
import re
import unicodedata
from typing import Literal

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


def _get_transliterate():
    """Lazy optional import for aksharamukha."""
    try:
        from aksharamukha import transliterate

        return transliterate
    except ImportError:
        log.warning("aksharamukha is not installed; script transliteration disabled.")
        return None


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
    """Format currency, percentages, and phone numbers with strict word boundaries.

    Prevents bugs like 'doctors 5' -> 'docto₹5'.
    Correctly converts:
    - 'Rs. 500', 'rupees 500', '500 rupees', '500 rupaya', 'rupaye 500' -> '₹500'
    - 'Rs 5 lakh', '5 lakh rupees', '५ लाख रुपये' -> '₹5 lakh', '₹५ लाख'
    - 'Rs 2.5 crore', '2 crore rupees', '२ करोड़ रुपये' -> '₹2.5 crore', '₹२ करोड़'
    - '५०० रुपये', '५०० रुपया', 'रु. 500' -> '₹५००', '₹500'
    - '50 percent', '50 per cent', '50 प्रतिशत' -> '50%'
    - '9876543210' -> '98765 43210'
    """
    if not text:
        return ""

    # 1. Lakh and Crore currency patterns (e.g. 'Rs 5 lakh', '5 lakh rupees', 'Rs. 2.5 crore')
    # Prefix: Rs / rupees / rupaya / rupaye + number + lakh / crore
    text = re.sub(
        r"\b(?:rupees?|rupaye?|rupaya|rs\.?)\s*(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)\b",
        r"₹\1 \2",
        text,
        flags=re.IGNORECASE,
    )
    # Suffix: number + lakh / crore + rupees / rupaye / rupaya / Rs
    text = re.sub(
        r"\b(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)\s*(?:rupees?|rupaye?|rupaya|rs\.?)\b",
        r"₹\1 \2",
        text,
        flags=re.IGNORECASE,
    )

    # 2. Devanagari Lakh / Crore currency patterns using proper lookarounds
    text = re.sub(
        r"(?<![\u0900-\u097F\w])(?:रुपये|रुपए|रुपया|रु\.?)\s*([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)\s*(लाख|करोड़)(?![\u0900-\u097F\w])",
        r"₹\1 \2",
        text,
    )
    text = re.sub(
        r"(?<![\u0900-\u097F\w])([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)\s*(लाख|करोड़)\s*(?:रुपये|रुपए|रुपया|रु\.?)(?![\u0900-\u097F\w])",
        r"₹\1 \2",
        text,
    )

    # 3. Standard prefix currency: "\b(?:rupees?|rupaye?|rupaya|rs\.?)\s*(\d...)"
    text = re.sub(
        r"\b(?:rupees?|rupaye?|rupaya|rs\.?)\s*(\d[\d,]*(?:\.\d+)?)",
        r"₹\1",
        text,
        flags=re.IGNORECASE,
    )

    # 4. Standard suffix currency: "(\d...)\s*\b(?:rupees?|rupaye?|rupaya|rs\.?)\b"
    text = re.sub(
        r"(\d[\d,]*(?:\.\d+)?)\s*\b(?:rupees?|rupaye?|rupaya|rs\.?)\b",
        r"₹\1",
        text,
        flags=re.IGNORECASE,
    )

    # 5. Standard Devanagari currency: 'रुपये ५००', '५०० रुपये', '५०० रुपया', 'रु. 500' using lookarounds
    text = re.sub(
        r"(?<![\u0900-\u097F\w])(?:रुपये|रुपए|रुपया|रु\.?)\s*([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)(?![\u0900-\u097F\w])",
        r"₹\1",
        text,
    )
    text = re.sub(
        r"(?<![\u0900-\u097F\w])([\d\u0966-\u096f,]+(?:\.[\d\u0966-\u096f]+)?)\s*(?:रुपये|रुपए|रुपया|रु\.?)(?![\u0900-\u097F\w])",
        r"₹\1",
        text,
    )

    # 6. Percentage formatting
    text = re.sub(
        r"\b(\d[\d,]*(?:\.\d+)?)\s*(?:per\s*cent|percent|प्रतिशत|टका)\b",
        r"\1%",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"([\u0966-\u096f]+(?:\.[\u0966-\u096f]+)?)\s*(?:प्रतिशत|टका)",
        r"\1%",
        text,
    )

    # 7. Indian 10-digit phone number formatting (e.g. 9876543210 -> 98765 43210, +91 98765 43210)
    def _format_phone(m: re.Match) -> str:
        prefix = m.group(1) or ""
        digits = m.group(2)
        return f"{prefix}{digits[:5]} {digits[5:]}"

    text = re.sub(
        r"(?:\b(\+91[\s-]?)|\b)([6-9]\d{9})\b",
        _format_phone,
        text,
    )

    return text


def apply_script_control(
    text: str, script: Literal["roman", "devanagari", "natural"] = "natural"
) -> str:
    """Apply verified offline script transliteration using Aksharamukha.

    - 'natural': keeps mixed script from STT output as-is (recommended for Hinglish).
    - 'roman': converts Devanagari/Gujarati script into phonetic Roman Latin script.
      Fixes the anusvara -> 'm' bug so 'हिंदी' converts to 'hindi' (not 'himdi').
      Does NOT run ITRANS on Roman text.
    - 'devanagari': [EXPERIMENTAL] converts Roman text into Devanagari via phonetic ITRANS.
    """
    if not text or script == "natural":
        return text

    transliterate = _get_transliterate()
    if transliterate is None:
        return text

    if script == "roman":
        try:
            has_deva = bool(re.search(r"[\u0900-\u097f]", text))
            has_guj = bool(re.search(r"[\u0a80-\u0aff]", text))
            if not has_deva and not has_guj:
                # Text is already Roman Latin — do NOT run ITRANS or alter Roman text
                return text

            if has_deva:
                trans = transliterate.process("Devanagari", "ISO", text)
            elif has_guj:
                trans = transliterate.process("Gujarati", "ISO", text)
            else:
                trans = text

            # Fix anusvara -> 'm' issue:
            # In ISO, anusvara can be '\u1e41' (dot above) or '\u1e43' (dot below).
            # Before labials (p, b), it is 'm'; before other consonants, it is 'n'.
            trans = re.sub(r"[\u1e41\u1e43]([pb])", r"m\1", trans, flags=re.IGNORECASE)
            trans = re.sub(r"[\u1e41\u1e43]", r"n", trans)

            # Map common ISO sibilants to standard English digraphs before stripping diacritics
            trans = re.sub(r"[śṣ]", r"sh", trans)
            trans = re.sub(r"[ŚṢ]", r"Sh", trans)

            # Strip diacritic accents for natural keyboard typing (e.g., bajē -> baje)
            decomposed = unicodedata.normalize("NFKD", trans)
            return "".join(c for c in decomposed if not unicodedata.combining(c))
        except Exception as e:
            log.warning("Roman transliteration failed: %s", e)
            return text

    if script == "devanagari":
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
