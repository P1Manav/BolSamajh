"""Robust multilingual sentence splitter for Hindi, Hinglish, and English.

Handles:
- Hindi Devanagari danda (।) and double danda (॥)
- Decimal numbers (e.g. 15.50, 3.14, ₹1,200.50, 99.9%)
- English abbreviations: Dr., Mr., Mrs., Ms., Prof., Rs., vs., approx., e.g., i.e., etc.
- Hindi abbreviations: डॉ., पं., रु., प्रो.
- Incremental streaming extraction for TTS pipelining.
"""

import re
from typing import List, Tuple, Optional

# Known abbreviations with trailing period (case-insensitive)
COMMON_ABBREVIATIONS = {
    "dr", "mr", "mrs", "ms", "prof", "sr", "jr", "rs", "vs", "approx",
    "eg", "ie", "etc", "no", "vol", "dept", "ltd", "corp", "inc",
    "st", "ave", "gen", "col", "gov",
    # Hindi abbreviations (without nukta / with nukta)
    "डॉ", "पं", "रु", "प्रो", "क्र",
}



def _is_abbreviation_or_decimal(text: str, match_start: int) -> bool:
    """Check if the period at match_start is part of a decimal number or abbreviation."""
    # 1. Decimal check: digit immediately before and after period (e.g. 15.50)
    if match_start > 0 and match_start + 1 < len(text):
        if text[match_start] == ".":
            prev_char = text[match_start - 1]
            next_char = text[match_start + 1]
            if prev_char.isdigit() and (next_char.isdigit() or next_char in ",%"):
                return True

    # 2. Abbreviation and initial check: look back up to 10 chars for preceding word
    if text[match_start] == ".":
        lookback = text[max(0, match_start - 10):match_start]
        m = re.search(r'([A-Za-z\u0900-\u097F]+)$', lookback)
        if m:
            raw_word = m.group(1)
            # Single-letter initials like "A.", "M.", "डॉ."
            if len(raw_word) == 1 and raw_word.isupper():
                return True
            word = raw_word.lower()
            if word in COMMON_ABBREVIATIONS:
                return True

    return False


def split_sentences(text: str) -> List[str]:
    """Split text into sentences handling Hindi danda, decimals, and abbreviations."""
    if not text or not text.strip():
        return []

    text = text.strip()
    sentences = []
    start = 0

    # Search for candidate terminators
    for match in re.finditer(r'([.?!।॥]|\n\n+)', text):
        pos = match.start()
        char = match.group(1)

        if char == "." and _is_abbreviation_or_decimal(text, pos):
            continue

        # Valid sentence terminator found
        end = match.end()
        # Include any consecutive punctuation (e.g. ... or !?)
        while end < len(text) and text[end] in ".?!।॥":
            end += 1
        # Include trailing closing quotes/brackets (e.g. "!", '?', .", .')
        while end < len(text) and text[end] in "\"'”’)]}":
            end += 1

        sentence = text[start:end].strip()
        if sentence:
            sentences.append(sentence)
        start = end

    # Remaining tail
    if start < len(text):
        tail = text[start:].strip()
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

    for match in re.finditer(r'([.?!।॥]+|\n\n+)(?:\s+|$)', buffer):
        pos = match.start()
        char = buffer[pos]

        if char == "." and _is_abbreviation_or_decimal(buffer, pos):
            continue

        # Valid sentence boundary
        end = match.end()
        # Include trailing closing quotes/brackets
        boundary_end = match.start() + len(match.group(1))
        while boundary_end < len(buffer) and buffer[boundary_end] in "\"'”’)]}":
            boundary_end += 1
        sentence = buffer[:boundary_end].strip()
        remaining = buffer[max(end, boundary_end):]
        if sentence:
            return sentence, remaining

    return None, buffer
