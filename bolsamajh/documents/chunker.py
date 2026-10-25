"""Document chunker — sentence-aware chunking with cross-page merging and format-specific citations."""

import logging
import re
from dataclasses import dataclass
from typing import List

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
        """Human-readable citation string conforming to document type.
        
        - 'Page N' only for PDFs.
        - 'Section: Name' or 'Paragraph N' for Web, DOCX, TXT, and Markdown.
        """
        is_pdf = self.source.lower().endswith(".pdf") or "pdf" in self.source.lower()
        parts = []

        if is_pdf and self.page_number:
            parts.append(f"Page {self.page_number}")
        elif not is_pdf:
            if self.section:
                parts.append(f"Section: {self.section}")
            else:
                parts.append(f"Paragraph {self.chunk_index + 1}")

        if not parts and self.section:
            parts.append(f"Section: {self.section}")

        return ", ".join(parts) if parts else f"Chunk {self.chunk_index + 1}"


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences handling Hindi (Devanagari danda) and English."""
    parts = re.split(r'(?<=[.!?।])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _estimate_tokens(text: str) -> int:
    """Estimate token count (~1.3 tokens per word for multilingual Hindi/English)."""
    words = len(text.split())
    return int(words * 1.3)


def chunk_document(
    document: Document,
    chunk_size: int = 380,
    chunk_overlap: int = 40,
) -> List[Chunk]:
    """Split a document into cross-page merged chunks aligned with 512-token embedders.
    
    Merges short paragraphs across pages to ensure dense, cohesive semantic chunks.
    """
    chunks: List[Chunk] = []
    chunk_index = 0

    current_sentences: List[str] = []
    current_tokens = 0
    current_page = 1
    current_section = ""
    current_source = document.source

    for page in document.pages:
        sentences = _split_into_sentences(page.text)
        if not sentences:
            continue

        for sentence in sentences:
            sent_tokens = _estimate_tokens(sentence)

            # If adding this sentence exceeds chunk_size, flush accumulated chunk
            if current_tokens + sent_tokens > chunk_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(Chunk(
                    text=chunk_text,
                    page_number=current_page,
                    section=current_section,
                    source=current_source,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

                # Overlap: preserve last few sentences up to chunk_overlap tokens
                overlap_sentences: List[str] = []
                overlap_tokens = 0
                for s in reversed(current_sentences):
                    s_tok = _estimate_tokens(s)
                    if overlap_tokens + s_tok > chunk_overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_tokens += s_tok

                current_sentences = overlap_sentences
                current_tokens = overlap_tokens

            # Append current sentence
            if not current_sentences:
                current_page = page.page_number
                current_section = page.section or current_section
                current_source = page.source or current_source

            current_sentences.append(sentence)
            current_tokens += sent_tokens

    # Flush remaining sentences
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append(Chunk(
            text=chunk_text,
            page_number=current_page,
            section=current_section,
            source=current_source,
            chunk_index=chunk_index,
        ))

    log.debug("Chunked document '%s' into %d chunks (size=%d, overlap=%d)",
              document.title, len(chunks), chunk_size, chunk_overlap)
    return chunks
