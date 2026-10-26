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

# Single digit word mappings for spoken numbers (English, Devanagari, Gujarati, and standard Roman Hindi)
SINGLE_DIGIT_WORDS = {
    # English
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    # Devanagari
    "शून्य": "0", "सुन्ना": "0", "सिफर": "0",
    "एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पाँच": "5", "पांच": "5",
    "छह": "6", "छः": "6", "सात": "7", "आठ": "8", "नौ": "9",
    # Gujarati
    "શૂન્ય": "0", "એક": "1", "બે": "2", "ત્રણ": "3", "ચાર": "4",
    "પાંચ": "5", "છ": "6", "સાત": "7", "આઠ": "8", "નવ": "9",
    # Standard Roman Hindi (real romanizations a human would write)
    "shunya": "0", "shoonya": "0",
    "ek": "1", "do": "2", "teen": "3", "tin": "3",
    "char": "4", "chaar": "4", "paanch": "5", "panch": "5",
    "chhe": "6", "chhah": "6", "chah": "6", "saat": "7", "sat": "7",
    "aath": "8", "ath": "8", "nau": "9",
}

# Unit numbers for compound number conversion
UNITS_MAP = {
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    # Devanagari
    "शून्य": 0, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9,
    "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    # Gujarati
    "શૂન્ય": 0, "એક": 1, "બે": 2, "ત્રણ": 3, "ચાર": 4, "પાંચ": 5, "છ": 6, "સાત": 7, "આઠ": 8, "નવ": 9, "દસ": 10,
    "વીસ": 20, "ત્રીસ": 30, "ચાલીસ": 40, "પચાસ": 50, "સાઇઠ": 60, "સિત્તેર": 70, "એંસી": 80, "નેવું": 90, "નેવુ": 90,
    # Standard Roman Hindi (real romanizations a human would write)
    "shunya": 0, "shoonya": 0,
    "ek": 1, "do": 2, "teen": 3, "tin": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5,
    "chhe": 6, "chhah": 6, "chah": 6, "saat": 7, "sat": 7, "aath": 8, "ath": 8, "nau": 9,
    "das": 10, "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16,
    "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20, "bis": 20, "tees": 30, "tis": 30, "chalis": 40,
    "pachaas": 50, "pachas": 50, "saath": 60, "sath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
}

# Scale multipliers with Indian lakh and crore support
SCALES_MAP = {
    # English
    "hundred": 100, "thousand": 1000, "lakh": 100000, "lakhs": 100000,
    "crore": 10000000, "crores": 10000000,
    # Devanagari
    "सौ": 100, "हज़ार": 1000, "हजार": 1000, "लाख": 100000, "करोड़": 10000000, "करोड": 10000000,
    # Gujarati
    "સો": 100, "હજાર": 1000, "લાખ": 100000, "કરોડ": 10000000,
    # Standard Roman Hindi
    "sau": 100, "so": 100,
    "hazaar": 1000, "hazar": 1000,
    "karod": 10000000,
}

# Ambiguous Roman words that collide with everyday English / grammatical words
AMBIGUOUS_ROMAN_WORDS = {"do", "so", "sat", "ath", "nau"}

# Scale words allowed to satisfy condition (b) for ambiguous word conversion
SCALE_WORDS_UNAMBIGUOUS = {
    "sau", "hazaar", "hazar", "lakh", "lakhs", "crore", "crores", "karod",
    "hundred", "thousand",
    "सौ", "हज़ार", "हजार", "लाख", "करोड़", "करोड",
    "સો", "હજાર", "લાખ", "કરોડ",
}

DECIMAL_SEPARATORS = {"point", "dashamlav", "दशमलव", "દશાંશ"}

SCALE_PRIORITY = {
    "crore": 4, "crores": 4, "karod": 4, "करोड़": 4, "करोड": 4, "કરોડ": 4,
    "lakh": 3, "lakhs": 3, "लाख": 3,
    "hazar": 2, "hazaar": 2, "thousand": 2, "हज़ार": 2, "हजार": 2, "હજાર": 2,
    "sau": 1, "so": 1, "hundred": 1, "सौ": 1, "સો": 1,
}

TENS_WORDS = {
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "bees", "bis", "tees", "tis", "chalis", "pachaas", "pachas", "saath", "sath",
    "sattar", "assi", "nabbe",
    "बीस", "तीस", "चालीस", "पचास", "साठ", "सत्तर", "अस्सी", "नब्बे",
    "વીસ", "ત્રીસ", "ચાલીસ", "પચાસ", "સાઇઠ", "સિત્તેર", "એંસી", "નેવું", "નેવુ",
}


def _parse_sub99(tokens: list, start_idx: int) -> tuple:
    """Parse a valid 1..99 numeric expression starting at start_idx."""
    if start_idx >= len(tokens):
        return None, start_idx
    tok = tokens[start_idx].lower()
    if tok.isdigit():
        val = int(tok)
        if 1 <= val <= 99:
            return val, start_idx + 1
        return None, start_idx
    if tok in TENS_WORDS:
        val = UNITS_MAP[tok]
        next_idx = start_idx + 1
        if next_idx < len(tokens):
            next_tok = tokens[next_idx].lower()
            if (
                next_tok in UNITS_MAP
                and 1 <= UNITS_MAP[next_tok] <= 9
                and next_tok not in TENS_WORDS
                and next_tok not in SCALE_PRIORITY
            ):
                val += UNITS_MAP[next_tok]
                return val, next_idx + 1
        return val, next_idx
    if tok in UNITS_MAP:
        val = UNITS_MAP[tok]
        if 1 <= val <= 19:
            return val, start_idx + 1
    return None, start_idx


def _parse_strict_number(tokens: list) -> tuple:
    """Parse tokens under strict grammar: scale periods in descending order + remainder.

    Returns (is_valid, total_value, tokens_consumed).
    """
    idx = 0
    total_val = 0
    last_scale_prio = 999

    while idx < len(tokens):
        tok = tokens[idx].lower()
        sub_val, next_idx = _parse_sub99(tokens, idx)
        if sub_val is not None:
            if next_idx < len(tokens) and tokens[next_idx].lower() in SCALE_PRIORITY:
                scale_tok = tokens[next_idx].lower()
                scale_prio = SCALE_PRIORITY[scale_tok]
                if scale_prio >= last_scale_prio:
                    return False, 0, 0
                scale_mult = SCALES_MAP[scale_tok]
                total_val += sub_val * scale_mult
                last_scale_prio = scale_prio
                idx = next_idx + 1
                continue
            else:
                total_val += sub_val
                idx = next_idx
                break
        elif tok in SCALE_PRIORITY:
            scale_prio = SCALE_PRIORITY[tok]
            if scale_prio >= last_scale_prio:
                return False, 0, 0
            scale_mult = SCALES_MAP[tok]
            total_val += scale_mult
            last_scale_prio = scale_prio
            idx += 1
        else:
            break

    if idx == 0:
        return False, 0, 0

    return True, total_val, idx


def normalize_numbers(text: str, normalize_number_words: bool = True) -> str:
    """Normalize numeric expressions across references and hypotheses.

    - Translates Indic digits (०-९, ૦-૯) to standard ASCII digits.
    - Strips commas between digits: 50,000 -> 50000.
    - Collapses spaced or hyphenated digit sequences: '9 8 7 6' -> '9876'.
    - If normalize_number_words is True:
        - Normalizes spoken decimals: 'tin dashamlav paanch' -> '3.5'.
        - Maps spoken single-digit word runs to digit strings: 'nau aath saat' -> '987'.
        - Converts Hindi/English compound number phrases under strict grammar: 'ek sau pachaas' -> '150'.
        - Protects ambiguous everyday words ('do', 'so', 'sat', 'ath', 'nau') unless in a valid
          grammar parse that includes a digit or scale word.
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

    if not normalize_number_words:
        return text

    # 4. Spoken decimals: "tin dashamlav paanch" -> "3.5", "3 point 5" -> "3.5"
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

    # 5. Sequences of single-digit words: e.g. "nau aath saat" -> "987"
    tokens = text.split()
    new_tokens = []
    i = 0
    while i < len(tokens):
        j = i
        run = []
        run_tokens = []
        while j < len(tokens) and (
            tokens[j].lower() in SINGLE_DIGIT_WORDS
            or (tokens[j].isdigit() and len(tokens[j]) == 1)
        ):
            tok_lower = tokens[j].lower()
            digit_val = SINGLE_DIGIT_WORDS.get(tok_lower, tokens[j])
            run.append(digit_val)
            run_tokens.append(tok_lower)
            j += 1

        if len(run) >= 2:
            ambig = [w for w in run_tokens if w in AMBIGUOUS_ROMAN_WORDS]
            if ambig:
                if len(run) >= 3:
                    new_tokens.append("".join(run))
                    i = j
                    continue
                has_digit = any(tok.isdigit() for tok in run_tokens)
                if has_digit:
                    new_tokens.append("".join(run))
                    i = j
                    continue
                new_tokens.append(tokens[i])
                i += 1
            else:
                new_tokens.append("".join(run))
                i = j
        else:
            new_tokens.append(tokens[i])
            i += 1
    text = " ".join(new_tokens)

    # 6. Compound numbers and strict number grammar parsing
    tokens = text.split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        j = i
        while j < len(tokens):
            t = tokens[j].lower()
            if t in UNITS_MAP or t in SCALES_MAP or t.isdigit():
                j += 1
            else:
                break

        if j == i:
            out_tokens.append(tokens[i])
            i += 1
            continue

        run = tokens[i:j]
        valid, val, end_idx = _parse_strict_number(run)

        # Must parse the WHOLE contiguous candidate run
        if not valid or end_idx != len(run):
            out_tokens.extend(run)
            i = j
            continue

        # Ambiguous words: {"do", "so", "sat", "ath", "nau"}
        ambig = [w for w in run if w.lower() in AMBIGUOUS_ROMAN_WORDS]
        has_digit = any(w.isdigit() for w in run)
        has_scale_unambig = any(w.lower() in SCALE_WORDS_UNAMBIGUOUS for w in run)
        has_unambig_tens_teens = any(
            w.lower() in UNITS_MAP and UNITS_MAP[w.lower()] >= 10 and w.lower() not in AMBIGUOUS_ROMAN_WORDS
            for w in run
        )

        if ambig and not (has_digit or has_scale_unambig or has_unambig_tens_teens):
            out_tokens.extend(run)
            i = j
            continue

        # Single word rule: leave single scale words and single units < 10 as words
        if len(run) == 1:
            tok = run[0].lower()
            if tok in SCALES_MAP or tok in AMBIGUOUS_ROMAN_WORDS:
                out_tokens.append(run[0])
                i = j
                continue
            if tok in UNITS_MAP and UNITS_MAP[tok] < 10 and not tok.isdigit():
                out_tokens.append(run[0])
                i = j
                continue

        out_tokens.append(str(val))
        i = j

    return " ".join(out_tokens)


def normalize_indic(text: str, normalize_number_words: bool = True) -> str:
    """Normalize Devanagari and Gujarati text to canonical form, preserving decimals."""
    if not text:
        return ""

    # Normalize numeric expressions first
    text = normalize_numbers(text, normalize_number_words=normalize_number_words)

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


def to_canonical_script(text: str, normalize_number_words: bool = True) -> str:
    """Convert mixed Indic/Latin text to a canonical Romanized script representation.

    This provides script-normalized evaluation by mapping Devanagari and Gujarati
    text to Roman ISO transliteration with diacritics stripped, ensuring cross-script
    comparability without claiming full phonemic loanword unification.
    Preserves decimals (e.g. 3.5, 36.6, 2.5 crore) and normalizes number expressions.
    """
    text = normalize_indic(text, normalize_number_words=normalize_number_words)
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
    text = normalize_numbers(text, normalize_number_words=normalize_number_words)

    return text


def compute_normalized_wer_cer(
    reference: str, hypothesis: str, normalize_number_words: bool = True
) -> Tuple[float, float, str, str]:
    """Calculate WER and CER between reference and hypothesis using canonical normalization.

    Args:
        reference: Ground truth transcript.
        hypothesis: Model predicted transcript.
        normalize_number_words: Whether to normalize spoken number words to numeric digits.

    Returns:
        (wer, cer, canonical_reference, canonical_hypothesis)
    """
    canon_ref = to_canonical_script(reference, normalize_number_words=normalize_number_words)
    canon_hyp = to_canonical_script(hypothesis, normalize_number_words=normalize_number_words)

    if not canon_hyp:
        wer = 1.0 if canon_ref else 0.0
        cer = 1.0 if canon_ref else 0.0
        return wer, cer, canon_ref, canon_hyp

    wer = float(jiwer.wer(canon_ref, canon_hyp))
    cer = float(jiwer.cer(canon_ref, canon_hyp))
    return wer, cer, canon_ref, canon_hyp

