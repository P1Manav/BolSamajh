"""Unit tests for sentence splitter handling abbreviations, decimals, and Hindi dandas."""

from bolsamajh.utils.sentence_splitter import split_sentences, extract_next_sentence


def test_split_sentences_numbers_and_decimals():
    """Verify numbers and decimals do not cause premature splits."""
    text = "The consultation fee is Rs. 15.50 today. The total cost reached ₹1,500.75 by evening."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert sentences[0] == "The consultation fee is Rs. 15.50 today."
    assert sentences[1] == "The total cost reached ₹1,500.75 by evening."

    pi_text = "Value of pi is approximately 3.14159 in mathematics."
    assert len(split_sentences(pi_text)) == 1


def test_split_sentences_english_abbreviations():
    """Verify Dr., Mr., Mrs., Rs., etc. do not split."""
    text = "Dr. Sharma and Mr. Verma met at approx. 5 PM. They reviewed the report with Mrs. Patel."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert sentences[0] == "Dr. Sharma and Mr. Verma met at approx. 5 PM."
    assert sentences[1] == "They reviewed the report with Mrs. Patel."


def test_split_sentences_hindi_danda_and_abbreviations():
    """Verify Hindi danda (।), double danda (॥), and Hindi abbreviations (डॉ., पं., रु.)."""
    text = "डॉ. शर्मा ने पं. नेहरू के विचार प्रस्तुत किए। क्या यह विचार सही हैं? उत्तर अवश्य दें॥"
    sentences = split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "डॉ. शर्मा ने पं. नेहरू के विचार प्रस्तुत किए।"
    assert sentences[1] == "क्या यह विचार सही हैं?"
    assert sentences[2] == "उत्तर अवश्य दें॥"


def test_extract_next_sentence_streaming():
    """Verify streaming incremental sentence extraction."""
    buffer = "Dr. Mehta paid Rs. 20.50 yesterday. Next topic is here."
    sent1, rem1 = extract_next_sentence(buffer)
    assert sent1 == "Dr. Mehta paid Rs. 20.50 yesterday."
    assert rem1 == "Next topic is here."

    sent2, rem2 = extract_next_sentence(rem1)
    assert sent2 == "Next topic is here."
    assert rem2 == ""

    # Incomplete sentence
    sent_inc, rem_inc = extract_next_sentence("Still speaking about Dr. Kumar")
    assert sent_inc is None
    assert rem_inc == "Still speaking about Dr. Kumar"
