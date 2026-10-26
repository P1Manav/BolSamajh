"""Unit tests for canonical normalization and transliteration scoring."""
import pytest
from bolsamajh.benchmark.normalization import (
    normalize_indic,
    normalize_numbers,
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


def test_decimal_preservation_and_word_edge_punctuation():
    # Decimal points between digits must be preserved
    assert to_canonical_script("3.5") == "3.5"
    assert to_canonical_script("36.6") == "36.6"
    assert to_canonical_script("2.5 crore") == "2.5 crore"
    assert to_canonical_script("Petrol rate kal se ₹1.50 per litre increase ho gaya hai.") == (
        "petrol rate kal se 1.50 per litre increase ho gaya hai"
    )

    # Word-edge periods (e.g. abbreviations, sentence ends) must be stripped
    assert to_canonical_script("Rs. 500.") == "rs 500"
    assert to_canonical_script("Order value was Rs. 150.") == "order value was rs 150"


def test_spaced_and_spoken_number_normalization():
    # Spaced and hyphenated digit runs collapsed into a single number
    assert to_canonical_script("9 8 7 6 5 4 3 2 1 0") == "9876543210"
    assert to_canonical_script("9-8-7-6-5-4-3-2-1-0") == "9876543210"

    # Spoken decimals
    assert to_canonical_script("tin dashamlav paanch") == "3.5"
    assert to_canonical_script("तीन दशमलव पांच") == "3.5"

    # Compound number words in Devanagari and Roman Hindi
    assert to_canonical_script("एक सौ पचास") == "150"
    assert to_canonical_script("ek sau pachaas") == "150"
    assert to_canonical_script("ek so pachas") == "150"


def test_number_word_grammar_and_ambiguity_guard():
    """All Tier 1 required tests: ambiguous Roman words protected, grammar-based conversion valid."""
    # Ambiguous Roman words protected (must remain unchanged)
    assert to_canonical_script("I do so like it") == "i do so like it"
    assert to_canonical_script("mujhe do teen din chahiye") == "mujhe do teen din chahiye"
    assert to_canonical_script("yeh sat ek baje") == "yeh sat ek baje"
    assert to_canonical_script("ath sat") == "ath sat"

    # Compound and spoken numbers converted to digits
    assert to_canonical_script("ek sau pachaas") == "150"
    assert to_canonical_script("one hundred fifty") == "150"
    assert to_canonical_script("tin dashamlav paanch") == "3.5"
    assert to_canonical_script("पचास") == "50"
    assert to_canonical_script("एक लाख") == "100000"

    # Preserved decimals and scales
    assert to_canonical_script("3.5") == "3.5"
    assert to_canonical_script("36.6") == "36.6"
    assert to_canonical_script("2.5 crore") == "2.5 crore"
    assert to_canonical_script("9 8 7 6 5 4 3 2 1 0") == "9876543210"


def test_normalize_number_words_flag():
    """Verify that normalize_number_words=False disables number word conversion while keeping digit normalization."""
    # When enabled (default):
    assert to_canonical_script("ek sau pachaas", normalize_number_words=True) == "150"
    assert to_canonical_script("पचास", normalize_number_words=True) == "50"

    # When disabled:
    assert to_canonical_script("ek sau pachaas", normalize_number_words=False) == "ek sau pachaas"
    # 'पचास' transliterates to 'pacasa' under ISO when not converted beforehand
    assert to_canonical_script("पचास", normalize_number_words=False) == "pacasa"

    # Digit collapsing still works even when normalize_number_words=False
    assert to_canonical_script("9 8 7 6 5 4 3 2 1 0", normalize_number_words=False) == "9876543210"
    assert to_canonical_script("3.5", normalize_number_words=False) == "3.5"


def test_no_fused_decimals_in_per_clip_results():
    """Regression test: verify no committed canonical reference fuses decimals into integers."""
    import json
    import re
    from pathlib import Path

    results_path = Path(__file__).resolve().parent.parent / "benchmark_data" / "per_clip_results.jsonl"
    if not results_path.exists():
        pytest.skip("per_clip_results.jsonl not present")

    decimal_pattern = re.compile(r"\b(\d+)\.(\d+)\b")
    fused_violations = []

    with open(results_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ref = rec.get("reference", "")
            canon_ref = rec.get("canonical_ref", "")

            # Check if reference contains a decimal like 3.5, 1.50, 24.5
            for m in decimal_pattern.finditer(ref):
                int_part, frac_part = m.group(1), m.group(2)
                original_decimal = f"{int_part}.{frac_part}"
                # The canonical reference must preserve the decimal, not fuse it into int_part + frac_part
                if original_decimal not in canon_ref:
                    fused_violations.append({
                        "line": idx,
                        "model": rec.get("model"),
                        "clip_id": rec.get("clip_id"),
                        "decimal": original_decimal,
                        "ref": ref,
                        "canonical_ref": canon_ref,
                    })

    assert not fused_violations, f"Found {len(fused_violations)} fused decimal references: {fused_violations[:5]}"


def test_phase3_strict_number_grammar_and_idempotence():
    """Phase 3 requirements:
    - 'nau do gyarah' (unchanged)
    - 'so do sau' (unchanged or only the valid sub-run)
    - 'do sau' -> 200
    - 'teen lakh' -> 300000
    - 'ek sau pachaas' -> 150
    - 'I do so like it' (unchanged)
    - Property-style test that normalization is idempotent
    """
    assert normalize_numbers("nau do gyarah") == "nau do gyarah"
    assert normalize_numbers("so do sau") in ("so do sau", "so 200")
    assert normalize_numbers("do sau") == "200"
    assert normalize_numbers("teen lakh") == "300000"
    assert normalize_numbers("ek sau pachaas") == "150"
    assert normalize_numbers("I do so like it") == "I do so like it"

    # Also verify via full canonical pipeline
    assert to_canonical_script("nau do gyarah") == "nau do gyarah"
    assert to_canonical_script("so do sau") in ("so do sau", "so 200")
    assert to_canonical_script("do sau") == "200"
    assert to_canonical_script("teen lakh") == "300000"
    assert to_canonical_script("ek sau pachaas") == "150"
    assert to_canonical_script("I do so like it") == "i do so like it"

    # Property-style idempotence test across representative phrases
    corpus = [
        "nau do gyarah",
        "so do sau",
        "do sau",
        "teen lakh",
        "ek sau pachaas",
        "I do so like it",
        "Total 3.5 crore rupees in account 9876543210 at Rs. 150 per unit.",
        "Flight 15th August ko subah 6:30 baje depart hogi",
        "Petrol rate kal se ₹1.50 per litre increase ho gaya hai.",
        "mujhe do teen din chahiye",
        "yeh sat ek baje",
        "ath sat",
        "ek so pachas",
        "one hundred fifty",
        "पचास",
        "एक लाख",
    ]
    for text in corpus:
        norm1 = normalize_numbers(text)
        norm2 = normalize_numbers(norm1)
        assert norm1 == norm2, f"normalize_numbers is not idempotent on {text!r}: {norm1!r} != {norm2!r}"

        canon1 = to_canonical_script(text)
        canon2 = to_canonical_script(canon1)
        assert canon1 == canon2, f"to_canonical_script is not idempotent on {text!r}: {canon1!r} != {canon2!r}"


