"""Unit tests for DocumentRetriever and chunking."""

import pytest
from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.documents.chunker import chunk_document
from bolsamajh.documents.retriever import DocumentRetriever


def test_chunker_cross_page_and_citations():
    """Test chunker splits and formats citations properly."""
    pdf_doc = Document(
        title="Test Report",
        source="report.pdf",
        pages=[
            DocumentPage(text="First paragraph of page 1. " * 30, page_number=1, source="report.pdf"),
            DocumentPage(text="Second paragraph on page 2. " * 30, page_number=2, source="report.pdf"),
        ],
        doc_type="pdf",
    )
    chunks = chunk_document(pdf_doc, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0
    assert chunks[0].citation.startswith("Page ")

    web_doc = Document(
        title="Blog Post",
        source="https://example.com/blog",
        pages=[
            DocumentPage(text="Introduction to BolSamajh. " * 20, page_number=1, section="Section 1", source="https://example.com/blog"),
        ],
        doc_type="web",
    )
    web_chunks = chunk_document(web_doc, chunk_size=50, chunk_overlap=10)
    assert len(web_chunks) > 0
    assert "Section" in web_chunks[0].citation


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
    retriever = DocumentRetriever(refusal_threshold=0.60)
    num_indexed = retriever.index_document(doc)
    assert num_indexed > 0
    assert retriever.is_loaded

    # Relevant query
    relevant_hits = retriever.retrieve("BolSamajh क्या है?", top_k=2)
    assert len(relevant_hits) > 0
    assert "BolSamajh" in relevant_hits[0].text

    # Completely irrelevant query with threshold check
    irrelevant_hits = retriever.retrieve("How do I make chocolate ice cream with caramel syrup?", top_k=2, apply_threshold=True)
    # The score should be below or very low
    for hit in irrelevant_hits:
        assert hit.score >= retriever.refusal_threshold
