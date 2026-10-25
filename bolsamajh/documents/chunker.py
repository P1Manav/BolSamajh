"""Document chunker — sentence-aware chunking with page/section tracking."""

import logging
import re
from dataclasses import dataclass

from bolsamajh.documents.loader import Document, DocumentPage

log = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of text with source metadata for citation."""
    text: str
    page_number: int = 0
    section: str = ""
    source: str = ""
    chunk_index: int = 0
    score: float = 0.0

    @property

    def citation(self) -> str:
        """Human-readable citation string."""
        parts = []
        if self.page_number:
            parts.append(f"Page {self.page_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        return ", ".join(parts) if parts else f"Chunk {self.chunk_index}"


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences (handles Hindi and English)."""
    # Split on sentence boundaries: . ? ! | (Devanagari danda)
    parts = re.split(r'(?<=[.!?।])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _estimate_tokens(text: str) -> int:
    """Rough token count estimate (~1.3 tokens per word for multilingual)."""
    words = len(text.split())
    return int(words * 1.3)


def chunk_document(
    document: Document,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Split a document into overlapping chunks for retrieval.

    Args:
        document: The loaded document.
        chunk_size: Target chunk size in tokens.
        chunk_overlap: Number of overlap tokens between chunks.

    Returns:
        List of Chunk objects with source metadata.
    """
    chunks = []
    chunk_index = 0

    for page in document.pages:
        sentences = _split_into_sentences(page.text)
        if not sentences:
            continue

        current_sentences: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sent_tokens = _estimate_tokens(sentence)

            if current_tokens + sent_tokens > chunk_size and current_sentences:
                # Save current chunk
                chunk_text = " ".join(current_sentences)
                chunks.append(Chunk(
                    text=chunk_text,
                    page_number=page.page_number,
                    section=page.section,
                    source=page.source,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

                # Overlap: keep last few sentences
                overlap_sentences: list[str] = []
                overlap_tokens = 0
                for s in reversed(current_sentences):
                    s_tok = _estimate_tokens(s)
                    if overlap_tokens + s_tok > chunk_overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_tokens += s_tok

                current_sentences = overlap_sentences
                current_tokens = overlap_tokens

            current_sentences.append(sentence)
            current_tokens += sent_tokens

        # Save last chunk for this page
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(Chunk(
                text=chunk_text,
                page_number=page.page_number,
                section=page.section,
                source=page.source,
                chunk_index=chunk_index,
            ))
            chunk_index += 1

    log.info("Chunked document '%s' into %d chunks (target=%d tokens)",
             document.title, len(chunks), chunk_size)
    return chunks
