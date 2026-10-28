"""Unit tests for DocumentRetriever and chunking."""

import pytest

from bolsamajh.documents.chunker import chunk_document
from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.documents.retriever import DocumentRetriever


def test_chunker_cross_page_and_citations():
    """Test chunker splits, formats citations, generates chunk_ids, and handles merged spans."""
    # 1. Multi-page PDF test
    pdf_doc = Document(
        title="Test Report",
        source="report.pdf",
        pages=[
            DocumentPage(
                text="First paragraph of page 1. Short ending.", page_number=1, source="report.pdf"
            ),
            DocumentPage(
                text="Second paragraph continuing on page 2.", page_number=2, source="report.pdf"
            ),
        ],
        doc_type="pdf",
    )
    # A single chunk that spans both page 1 and page 2
    chunks = chunk_document(pdf_doc, chunk_size=300, chunk_overlap=10)
    assert len(chunks) == 1
    # Check chunk_id instead of loose substring
    assert chunks[0].chunk_id == "report.pdf_chunk_0"
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert chunks[0].citation == "Pages 1–2"

    # 2. Web doc test (must never be called 'Page')
    web_doc = Document(
        title="Blog Post",
        source="https://example.com/blog",
        pages=[
            DocumentPage(
                text="Introduction to BolSamajh. " * 20,
                page_number=1,
                section="Section 1",
                source="https://example.com/blog",
            ),
        ],
        doc_type="web",
    )
    web_chunks = chunk_document(web_doc, chunk_size=50, chunk_overlap=10)
    assert len(web_chunks) > 0
    assert web_chunks[0].chunk_id == "blog_chunk_0"
    assert web_chunks[0].citation.startswith("Section")
    assert not web_chunks[0].citation.startswith("Page")


@pytest.mark.slow
def test_retriever_indexing_and_refusal():
    """Test DocumentRetriever indexing and threshold filtering."""
    doc = Document(
        title="AI Overview",
        source="ai.txt",
        pages=[
            DocumentPage(
                text="कृत्रिम बुद्धिमत्ता (Artificial Intelligence) कंप्यूटर विज्ञान की एक शाखा है जो मशीनों को बुद्धिमान बनाती है। "
                "BolSamajh एक बहुभाषी वॉयस-एआई असिस्टेंट है जो हिंदी और हिंग्लिश को समझता है।",
                page_number=1,
                section="Section 1",
                source="ai.txt",
            )
        ],
        doc_type="txt",
    )
    retriever = DocumentRetriever(refusal_threshold=0.785)
    num_indexed = retriever.index_document(doc)
    assert num_indexed > 0
    assert retriever.is_loaded

    # Relevant query
    relevant_hits = retriever.retrieve("BolSamajh क्या है?", top_k=2)
    assert len(relevant_hits) > 0
    assert "BolSamajh" in relevant_hits[0].text

    # Completely irrelevant query with threshold check: should return 0 hits
    irrelevant_hits = retriever.retrieve(
        "How do I make chocolate ice cream with caramel syrup?", top_k=2, apply_threshold=True
    )
    assert len(irrelevant_hits) == 0

    # Without threshold, raw top score should be strictly below refusal threshold
    raw_hits = retriever.retrieve(
        "How do I make chocolate ice cream with caramel syrup?", top_k=2, apply_threshold=False
    )
    assert len(raw_hits) > 0
    assert raw_hits[0].score < retriever.refusal_threshold
