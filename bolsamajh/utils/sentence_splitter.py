"""Robust multilingual sentence splitter for Hindi, Hinglish, and English.

Handles:
- Hindi Devanagari danda (।) and double danda (॥)
- Decimal numbers (e.g. 15.50, 3.14, ₹1,200.50, 99.9%)
- Times (e.g. 10:30, 09:15 AM)
- English abbreviations: Dr., Mr., Mrs., Ms., Prof., Rs., vs., approx., e.g., i.e., etc.
- Hindi abbreviations: डॉ., पं., रु., प्रो.
- List items and newline boundaries
- Incremental streaming extraction for TTS pipelining.
"""

import re
from typing import List, Optional, Tuple

# Curated unambiguous abbreviations with trailing period (case-insensitive)
# Note: words like 'no', 'st', 'col', 'gen', 'vol' that frequently end sentences are excluded.
COMMON_ABBREVIATIONS = {
    "dr",
    "mr",
    "mrs",
    "ms",
    "prof",
    "sr",
    "jr",
    "rs",
    "vs",
    "approx",
    "eg",
    "ie",
    "etc",
    "dept",
    "ltd",
    "corp",
    "inc",
    "ave",
    "gov",
    # Hindi abbreviations
    "डॉ",
    "पं",
    "रु",
    "प्रो",
    "क्र",
}


def _is_abbreviation_or_decimal(text: str, match_start: int) -> bool:
    """Check if the period at match_start is part of a decimal number, time, list item, or abbreviation."""
    if text[match_start] != ".":
        return False

    # 1. List item numbering check (e.g. '1. First item' or '\n2. Second item')
    m_num = re.search(r"(?:^|[\s\n])(\d+)$", text[:match_start])
    if m_num:
        if match_start + 1 < len(text) and text[match_start + 1] in " \t":
            return True

    # 2. Decimal number check:
    # If digit precedes period:
    if match_start > 0 and text[match_start - 1].isdigit():
        if match_start + 1 < len(text):
            next_char = text[match_start + 1]
            if next_char.isdigit() or next_char in ",%":
                return True
        else:
            # Trailing period preceded by digit at end of buffer: cannot confirm boundary yet
            return True

    # 3. Single-letter initial check (e.g. 'a.', 'm.', 'J.') and abbreviations
    lookback = text[max(0, match_start - 10) : match_start]
    m = re.search(r"([A-Za-z\u0900-\u097F]+)$", lookback)
    if m:
        raw_word = m.group(1)
        if len(raw_word) == 1:
            return True
        word = raw_word.lower()
        if word in COMMON_ABBREVIATIONS:
            return True

    # 4. Lookforward confirmation: if following non-whitespace character is a lowercase letter,
    # it is an intra-sentence period (e.g. 'a.m. today', 'i.e. example') and not a sentence boundary.
    rest = text[match_start + 1 :].lstrip(" \t\"'”’)]}")
    if rest and rest[0].islower():
        return True

    return False


def split_sentences(text: str) -> List[str]:
    """Split text into sentences handling Hindi danda, decimals, times, abbreviations, newlines, and list items."""
    if not text or not text.strip():
        return []

    text = text.strip()

    # Split on newlines followed by list markers or double newlines first
    chunks = re.split(r"(\n+\s*(?:[-*•]|\d+\.)\s*|\n\n+)", text)
    segments = []
    current = ""
    for part in chunks:
        if re.match(r"^\n+\s*(?:[-*•]|\d+\.)\s*$", part):
            if current.strip():
                segments.append(current.strip())
            current = part.strip() + " "
        elif re.match(r"^\n\n+$", part):
            if current.strip():
                segments.append(current.strip())
            current = ""
        else:
            current += part
    if current.strip():
        segments.append(current.strip())

    sentences = []
    for segment in segments:
        start = 0
        for m in re.finditer(r"([.?!।॥]+)(?:\s+|$)", segment):
            token = m.group(1)
            pos = m.start()
            if "." in token and _is_abbreviation_or_decimal(segment, pos + token.index(".")):
                continue
            end = m.end()
            s = segment[start:end].strip()
            if s:
                sentences.append(s)
            start = end
        if start < len(segment):
            tail = segment[start:].strip()
            if tail:
                sentences.append(tail)

    return sentences


def extract_next_sentence(buffer: str) -> Tuple[Optional[str], str]:
    """Incremental sentence extractor for streaming LLM generation.

    Returns:
        (completed_sentence, remaining_buffer)
        If no completed sentence is found yet, returns (None, buffer).
    """
    if not buffer:
        return None, buffer

    # Look for boundary followed by whitespace, newline, or end-of-sentence list markers
    pattern = re.compile(r"([.?!।॥]+|\n+\s*(?:[-*•]|\d+\.)\s*|\n\n+)(?:\s+|$)")

    for match in pattern.finditer(buffer):
        pos = match.start()
        token = match.group(1)

        if "." in token:
            period_idx = pos + token.index(".")
            if _is_abbreviation_or_decimal(buffer, period_idx):
                continue
            # If period is preceded by digit, do not treat as boundary until next non-digit confirms it
            if period_idx > 0 and buffer[period_idx - 1].isdigit():
                if period_idx + 1 >= len(buffer) or buffer[period_idx + 1].isdigit():
                    continue

        boundary_end = match.start() + len(token)
        while boundary_end < len(buffer) and buffer[boundary_end] in "\"'”’)]}":
            boundary_end += 1

        sentence = buffer[:boundary_end].strip()
        remaining = buffer[max(match.end(), boundary_end) :]
        if sentence:
            return sentence, remaining

    return None, buffer
