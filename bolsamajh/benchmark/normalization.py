"""Canonical Indic text normalization and transliteration scoring.

Adheres to Tier 1 Requirement 6:
- Normalizes Devanagari/Gujarati: nuktas, chandrabindu/anusvara, dandas, digit forms.
- Eliminates zero-width formatting characters (ZWJ, ZWNJ).
- Transliterates into a canonical phonemic script (ISO/ITRANS) using Aksharamukha,
  so spelling variants of English loanwords and code-switching are evaluated
  on phonetic fidelity rather than character-set mismatches.
- Drops the unprincipled 'best of two references' trick in favor of a single canonical evaluation.
"""

import re
import unicodedata
from typing import Tuple

import jiwer
from aksharamukha import transliterate


# Indic to ASCII digit translation map
DIGIT_MAP = str.maketrans(
    "०१२३४५६७८९૦૧૨૩૪૫૬૭૮૯",
    "01234567890123456789"
)

# Punctuation and dandas regex
PUNCT_REGEX = re.compile(r"[\u0964\u0965।,!?;:\-\"\'\(\)\[\]\{\}\/\\`~@#$%^&*+=<>_]")

# Zero-width formatting characters
ZERO_WIDTH_REGEX = re.compile(r"[\u200b\u200c\u200d\ufeff]")

# Devanagari and Gujarati nuktas
NUKTA_REGEX = re.compile(r"[\u093c\u0abc]")


def normalize_indic(text: str) -> str:
    """Normalize Devanagari and Gujarati text to canonical form."""
    if not text:
        return ""
    
    # 1. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)
    
    # 2. Convert Indic digits to standard ASCII digits
    text = text.translate(DIGIT_MAP)
    
    # 3. Chandrabindu (\u0901) -> Anusvara (\u0902)
    text = text.replace("\u0901", "\u0902")
    # Gujarati chandrabindu (\u0a81) -> anusvara (\u0a82)
    text = text.replace("\u0a81", "\u0a82")
    
    # 4. Strip nukta to avoid artificial mismatches (e.g. ख़ vs ख, ज़ vs ज)
    text = NUKTA_REGEX.sub("", text)
    
    # 5. Remove zero-width characters
    text = ZERO_WIDTH_REGEX.sub("", text)
    
    # 6. Remove dandas and punctuation
    text = PUNCT_REGEX.sub(" ", text)
    
    # 7. Lowercase and collapse whitespace
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def to_canonical_script(text: str) -> str:
    """Convert mixed Indic/Latin text to a canonical Romanized phonemic representation.
    
    This ensures that English words transcribed into Devanagari (e.g. मीटिंग)
    and English words in Latin script (e.g. meeting) are evaluated fairly
    in a canonical phonemic script.
    """
    text = normalize_indic(text)
    if not text:
        return ""
    
    # Check if text contains Devanagari characters (\u0900-\u097f)
    has_deva = bool(re.search(r"[\u0900-\u097f]", text))
    has_guj = bool(re.search(r"[\u0a80-\u0aff]", text))
    
    if has_deva:
        try:
            text = transliterate.process("Devanagari", "ISO", text)
        except Exception:
            pass
    elif has_guj:
        try:
            text = transliterate.process("Gujarati", "ISO", text)
        except Exception:
            pass
            
    # Normalize ISO diacritics to basic Latin base characters for fair ASR loanword scoring
    # e.g., mīṭiṅga -> mitinga
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    
    # Final cleanup of any lingering artifacts
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    
    return text


def compute_normalized_wer_cer(reference: str, hypothesis: str) -> Tuple[float, float, str, str]:
    """Calculate WER and CER between reference and hypothesis using canonical normalization.
    
    Returns:
        (wer, cer, canonical_reference, canonical_hypothesis)
    """
    canon_ref = to_canonical_script(reference)
    canon_hyp = to_canonical_script(hypothesis)
    
    if not canon_hyp:
        wer = 1.0 if canon_ref else 0.0
        cer = 1.0 if canon_ref else 0.0
        return wer, cer, canon_ref, canon_hyp
        
    wer = float(jiwer.wer(canon_ref, canon_hyp))
    cer = float(jiwer.cer(canon_ref, canon_hyp))
    return wer, cer, canon_ref, canon_hyp
