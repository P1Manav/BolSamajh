"""Unit tests for text_cleanup: currency regex, filler preservation, and script control."""

from bolsamajh.utils.text_cleanup import (
    apply_script_control,
    format_numbers,
    remove_fillers,
)


def test_currency_word_boundary_edge_cases():
    # The critical bug: 'doctors 5' must NOT become 'docto₹5'
    assert format_numbers("There were doctors 5 years ago") == "There were doctors 5 years ago"
    assert format_numbers("Call the doctors 5 times") == "Call the doctors 5 times"
    assert format_numbers("users 10 reported errors") == "users 10 reported errors"

    # Legitimate currency formatting
    assert format_numbers("Total bill is Rs. 500") == "Total bill is ₹500"
    assert format_numbers("Total bill is Rs 500") == "Total bill is ₹500"
    assert format_numbers("Pay 500 rupees now") == "Pay ₹500 now"
    assert format_numbers("Cost is 1,299 rupees") == "Cost is ₹1,299"
    assert format_numbers("Price is rupaye 450") == "Price is ₹450"

    # Devanagari currency formatting
    assert "₹500" in format_numbers("किराया 500 रुपये है") or "₹५००" in format_numbers(
        "किराया ५०० रुपये है"
    )


def test_filler_patterns_preserve_real_words():
    # Real words must NEVER be removed
    text_like = "I like this architecture"
    assert "like" in remove_fillers(text_like)

    text_sun = "The sun rises in the east and sun is bright"
    assert "sun" in remove_fillers(text_sun)

    text_so = "So what did the team decide?"
    assert "So" in remove_fillers(text_so) or "so" in remove_fillers(text_so)

    text_actually = "This actually works very well"
    assert "actually" in remove_fillers(text_actually)

    text_matlab = "Iska matlab kya hota hai?"
    assert "matlab" in remove_fillers(text_matlab)

    text_dekho = "Dekho screen par kya likha hai"
    assert "Dekho" in remove_fillers(text_dekho) or "dekho" in remove_fillers(text_dekho)

    text_toh = "Yeh toh bohot accha hai"
    assert "toh" in remove_fillers(text_toh)

    text_accha = "Accha kaam kiya aapne"
    assert "Accha" in remove_fillers(text_accha) or "accha" in remove_fillers(text_accha)


def test_true_disfluencies_removed():
    # Vocal hesitations SHOULD be removed
    assert remove_fillers("I umm think uhh we should start") == "I think we should start"
    assert remove_fillers("hmm let me check aah okay") == "let me check okay"
    assert remove_fillers("उम्म मुझे लगता है हम्म यह सही है") == "मुझे लगता है यह सही है"


def test_script_control():
    # Natural mode leaves text intact
    assert apply_script_control("मीटिंग 3:45 बजे है", script="natural") == "मीटिंग 3:45 बजे है"

    # Roman mode transliterates Devanagari cleanly (NOT 'maeetainga')
    roman_out = apply_script_control("मीटिंग 3:45 बजे है", script="roman")
    assert "maeetainga" not in roman_out.lower()
    assert "mīṭiṅga" in roman_out or "miting" in roman_out.lower() or "baje" in roman_out.lower()

    # Devanagari mode converts Roman Hindi
    deva_out = apply_script_control("namaste", script="devanagari")
    assert "नमस्ते" in deva_out or any("\u0900" <= c <= "\u097f" for c in deva_out)
