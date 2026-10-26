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

