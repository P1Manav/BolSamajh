"""Unit tests for canonical normalization and transliteration scoring."""
import pytest
from bolsamajh.benchmark.normalization import (
    normalize_indic,
    to_canonical_script,
    compute_normalized_wer_cer,
)


def test_digit_normalization():
    # Devanagari digits to ASCII (punctuation stripped)
    cleaned = normalize_indic("३:४५")
    assert "3 45" in cleaned or ("3" in cleaned and "45" in cleaned)
    # Gujarati digits to ASCII
    assert "1299" in normalize_indic("૧૨૯૯")


def test_danda_and_punctuation_removal():
    cleaned = normalize_indic("नमस्ते। आप कैसे हैं? सब ठीक!")
    assert "।" not in cleaned
    assert "?" not in cleaned
    assert "!" not in cleaned


def test_nukta_and_chandrabindu():
    # Nukta stripped
    cleaned = normalize_indic("फ़ोन और क़लम")
    assert "\u093c" not in cleaned
    # Chandrabindu mapped to anusvara
    mapped = normalize_indic("हूँ")
    assert "\u0901" not in mapped


def test_canonical_transliteration():
    canon1 = to_canonical_script("मीटिंग 3:45 बजे स्टार्ट होगी")
    canon2 = to_canonical_script("meeting 3:45 baje start hogi")
    # Both should be romanized and lowercase
    assert canon1.replace(" ", "") != ""
    assert canon2.replace(" ", "") != ""


def test_compute_normalized_wer_cer():
    wer, cer, cref, chyp = compute_normalized_wer_cer(
        "Flight 15th August ko subah 6:30 baje depart hogi",
        "Flight 15th August ko subah 6:30 baje depart hogi"
    )
    assert wer == 0.0
    assert cer == 0.0
