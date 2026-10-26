"""Canonical Indic text normalization and script-normalized transliteration scoring.

Adheres strictly to benchmark credibility standards:
- Normalizes Devanagari/Gujarati: nuktas, chandrabindu/anusvara, dandas, digit forms.
- Eliminates zero-width formatting characters (ZWJ, ZWNJ).
- Decimal preservation: preserves '.' between digits (e.g. 3.5, 36.6, 2.5 crore) while stripping word-edge punctuation.
- Number normalization: collapses spaced/hyphenated digits and converts spoken Hindi/English number words to digits.
- Transliterates Indic scripts (Devanagari/Gujarati) into canonical ASCII-Roman (ISO transliteration
  with diacritic stripping via Aksharamukha). Note: this bridges cross-script representation
  (Devanagari vs Roman), but is designated as 'script-normalized WER' rather than 'phonemic'
  because loanword orthography differences (e.g. English 'meeting' vs transliterated 'mitinga')
  are not phonemically merged.
- Drops the unprincipled 'best of two references' trick in favor of single canonical evaluation.
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

# Punctuation and dandas regex (excluding periods between digits)
PUNCT_REGEX = re.compile(r"[\u0964\u0965।,!?;:\-\"\'\(\)\[\]\{\}\/\\`~@#$%^&*+=<>_]")

# Zero-width formatting characters
ZERO_WIDTH_REGEX = re.compile(r"[\u200b\u200c\u200d\ufeff]")

# Devanagari and Gujarati nuktas
NUKTA_REGEX = re.compile(r"[\u093c\u0abc]")

# Single digit word mappings for spoken numbers (English, Devanagari, and Roman Hinglish)
SINGLE_DIGIT_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "शून्य": "0", "सुन्ना": "0", "सिफर": "0",
    "एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पाँच": "5", "पांच": "5",
    "छह": "6", "छः": "6", "सात": "7", "आठ": "8", "नौ": "9",
    "shunya": "0", "shoonya": "0", "shoony": "0", "sunya": "0",
    "ek": "1", "eka": "1", "do": "2", "teen": "3", "tin": "3", "tina": "3",
    "chaar": "4", "char": "4", "cara": "4", "paanch": "5", "panch": "5",
    "pamca": "5", "chhah": "6", "chhe": "6", "chah": "6", "saat": "7",
    "sat": "7", "sata": "7", "aath": "8", "ath": "8", "atha": "8",
    "nau": "9", "nav": "9", "nava": "9",
}

# Unit numbers for compound number conversion
UNITS_MAP = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    # Devanagari
    "शून्य": 0, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9,
    "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    # Roman Hindi
    "ek": 1, "eka": 1, "do": 2, "teen": 3, "tin": 3, "tina": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5,
    "chhah": 6, "chhe": 6, "saat": 7, "sat": 7, "aath": 8, "ath": 8, "nau": 9,
    "das": 10, "dasa": 10, "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16,
    "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20, "bis": 20, "tees": 30, "tis": 30, "chalis": 40,
    "pachaas": 50, "pachas": 50, "pacasa": 50, "saath": 60, "sath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
}

# Scale multipliers with Indian lakh and crore support
SCALES_MAP = {
    "hundred": 100, "सौ": 100, "सो": 100, "sau": 100, "so": 100,
    "thousand": 1000, "हज़ार": 1000, "हजार": 1000, "hazar": 1000, "hazaar": 1000, "hajara": 1000,
    "lakh": 100000, "lakhs": 100000, "लाख": 100000, "lakha": 100000,
    "crore": 10000000, "crores": 10000000, "करोड़": 10000000, "करोड": 10000000, "karod": 10000000, "karoda": 10000000,
}

DECIMAL_SEPARATORS = {"point", "dashamlav", "dashamla", "dasamla", "dasamlav", "दशमलव"}


def normalize_numbers(text: str) -> str:
    """Normalize numeric expressions across references and hypotheses.

    - Translates Indic digits (०-९, ૦-૯) to standard ASCII digits.
    - Strips commas between digits: 50,000 -> 50000.
    - Collapses spaced or hyphenated digit sequences: '9 8 7 6' -> '9876'.
    - Normalizes spoken decimals: 'tin dashamlav paanch' -> '3.5', '3 dasamla 5' -> '3.5'.
    - Maps spoken single-digit word runs to digit strings: 'nau aath saat' -> '987'.
    - Converts Hindi/English compound number phrases: 'ek sau pachaas' -> '150'.
    """
    if not text:
        return ""

    # 1. Convert Indic digits to standard ASCII digits
    text = text.translate(DIGIT_MAP)

    # 2. Strip commas within numbers (e.g. 50,000 -> 50000, 1,299 -> 1299)
    text = re.sub(r'(?<=\d),(?=\d)', '', text)

    # 3. Collapse spaced/hyphenated digit runs: "9 8 7 6" or "9-8-7-6" -> "9876"
    digit_run_pattern = re.compile(r'\b\d(?:[\s\-]+\d)+\b')
    prev = ""
    while prev != text:
        prev = text
        text = digit_run_pattern.sub(lambda m: re.sub(r'[\s\-]+', '', m.group(0)), text)

    # 4. Spoken decimals: "tin dashamlav paanch" -> "3.5", "3 dasamla 5" -> "3.5"
    words = text.split()
    out_words = []
    i = 0
    while i < len(words):
        if (
            i + 2 < len(words)
            and words[i+1].lower() in DECIMAL_SEPARATORS
        ):
            w1 = words[i].lower()
            w2 = words[i+2].lower()
            d1 = SINGLE_DIGIT_WORDS.get(w1, w1 if w1.isdigit() else None)
            d2 = SINGLE_DIGIT_WORDS.get(w2, w2 if w2.isdigit() else None)
            if d1 is not None and d2 is not None:
                out_words.append(f"{d1}.{d2}")
                i += 3
                continue
        out_words.append(words[i])
        i += 1
    text = " ".join(out_words)

    # 5. Sequences of single-digit words: e.g. "nau aath saat chhah paanch chaar tin do ek shoony"
    tokens = text.split()
    new_tokens = []
    i = 0
    while i < len(tokens):
        j = i
        run = []
        while j < len(tokens) and tokens[j].lower() in SINGLE_DIGIT_WORDS:
            run.append(SINGLE_DIGIT_WORDS[tokens[j].lower()])
            j += 1
        if len(run) >= 2:
            new_tokens.append("".join(run))
            i = j
        else:
            new_tokens.append(tokens[i])
            i += 1
    text = " ".join(new_tokens)

    # 6. Compound numbers (e.g. "ek sau pachaas" -> "150", "one hundred fifty" -> "150")
    tokens = text.split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        sub_i = i
        current_val = 0
        total_val = 0
        has_compound = False
        words_count = 0

        while sub_i < len(tokens):
            tok = tokens[sub_i].lower()
            if tok in UNITS_MAP:
                current_val += UNITS_MAP[tok]
                words_count += 1
                sub_i += 1
            elif tok in SCALES_MAP:
                scale = SCALES_MAP[tok]
                if current_val == 0:
                    current_val = 1
                if scale >= 1000:
                    total_val += current_val * scale
                    current_val = 0
                else:
                    current_val *= scale
                has_compound = True
                words_count += 1
                sub_i += 1
            elif tok.isdigit() and sub_i + 1 < len(tokens) and tokens[sub_i + 1].lower() in SCALES_MAP:
                current_val += int(tok)
                words_count += 1
                sub_i += 1
            else:
                break

        total_val += current_val
        if has_compound and words_count >= 2:
            out_tokens.append(str(total_val))
            i = sub_i
        elif words_count >= 2 and current_val > 0:
            out_tokens.append(str(total_val))
            i = sub_i
        else:
            out_tokens.append(tokens[i])
            i += 1

    return " ".join(out_tokens)


def normalize_indic(text: str) -> str:
    """Normalize Devanagari and Gujarati text to canonical form, preserving decimals."""
    if not text:
        return ""

    # Normalize numeric expressions first
    text = normalize_numbers(text)

    # 1. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 2. Chandrabindu (\u0901) -> Anusvara (\u0902)
    text = text.replace("\u0901", "\u0902")
    # Gujarati chandrabindu (\u0a81) -> anusvara (\u0a82)
    text = text.replace("\u0a81", "\u0a82")

    # 3. Strip nukta to avoid artificial mismatches (e.g. ख़ vs ख, ज़ vs ज)
    text = NUKTA_REGEX.sub("", text)

    # 4. Remove zero-width characters
    text = ZERO_WIDTH_REGEX.sub("", text)

    # 5. Remove dandas and punctuation, preserving decimal points between digits
    text = PUNCT_REGEX.sub(" ", text)

    # 6. Strip periods only at word edges / not between digits
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text)

    # 7. Lowercase and collapse whitespace
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()

    return text


def to_canonical_script(text: str) -> str:
    """Convert mixed Indic/Latin text to a canonical Romanized script representation.

    This provides script-normalized evaluation by mapping Devanagari and Gujarati
    text to Roman ISO transliteration with diacritics stripped, ensuring cross-script
    comparability without claiming full phonemic loanword unification.
    Preserves decimals (e.g. 3.5, 36.6, 2.5 crore) and normalizes number expressions.
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

    # Final cleanup: preserve alphanumeric, whitespace, and period between digits
    text = re.sub(r"[^a-zA-Z0-9\s\.]", " ", text)
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()

    # Re-normalize any numbers transliterated from Indic
    text = normalize_numbers(text)

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

