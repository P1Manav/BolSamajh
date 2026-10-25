"""Document chunker — sentence-aware chunking with cross-page merging and format-specific citations."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from bolsamajh.documents.loader import Document, DocumentPage
from bolsamajh.utils.sentence_splitter import split_sentences

log = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of text with source metadata for citation."""
    text: str
    page_number: int = 0
    page_start: int = 0
    page_end: int = 0
    section: str = ""
    section_start: int = 0
    section_end: int = 0
    source: str = ""
    chunk_index: int = 0
    chunk_id: str = ""
    score: float = 0.0
    doc_type: str = ""

    def __post_init__(self):
        if not self.page_start and self.page_number:
            self.page_start = self.page_number
        if not self.page_end and self.page_number:
            self.page_end = self.page_number
        if not self.chunk_id:
            src_name = Path(self.source).name if self.source else "doc"
            self.chunk_id = f"{src_name}_chunk_{self.chunk_index}"

    @property
    def citation(self) -> str:
        """Human-readable citation string conforming to document type.
        
        - PDFs: 'Page X' or 'Pages X–Y' for merged cross-page chunks (never 'section').
        - DOCX, Web, TXT, MD: 'Section X' or 'Sections X–Y' or 'Section: Title' (never 'Page').
        """
        is_pdf = (
            self.doc_type == "pdf" or 
            self.source.lower().endswith(".pdf") or 
            "pdf" in self.source.lower()
        )

        if is_pdf:
            start = self.page_start or self.page_number
            end = self.page_end or self.page_number
            if start and end and start != end:
                return f"Pages {start}–{end}"
            elif start:
                return f"Page {start}"
            return f"Chunk {self.chunk_index + 1}"

        # DOCX, Web, TXT, Markdown: strictly 'Section'
        if self.section:
            if not self.section.lower().startswith("section"):
                return f"Section: {self.section}"
            return self.section
        elif self.section_start and self.section_end and self.section_start != self.section_end:
            return f"Sections {self.section_start}–{self.section_end}"
        elif self.section_start:
            return f"Section {self.section_start}"
        return f"Section {self.chunk_index + 1}"


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
    
    Merges short paragraphs across pages and records full page spans (e.g. Pages 1-2).
    """
    chunks: List[Chunk] = []
    chunk_index = 0

    current_sentences: List[str] = []
    current_tokens = 0
    chunk_page_start = 0
    chunk_page_end = 0
    chunk_sec_start = 0
    chunk_sec_end = 0
    current_section = ""
    current_source = document.source

    for page in document.pages:
        sentences = split_sentences(page.text)
        if not sentences:
            continue

        for sentence in sentences:
            sent_tokens = _estimate_tokens(sentence)

            # If adding this sentence exceeds chunk_size, flush accumulated chunk
            if current_tokens + sent_tokens > chunk_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                src_name = Path(current_source).name if current_source else "doc"
                chunks.append(Chunk(
                    text=chunk_text,
                    page_number=chunk_page_start,
                    page_start=chunk_page_start,
                    page_end=chunk_page_end,
                    section=current_section,
                    section_start=chunk_sec_start,
                    section_end=chunk_sec_end,
                    source=current_source,
                    chunk_index=chunk_index,
                    chunk_id=f"{src_name}_chunk_{chunk_index}",
                    doc_type=document.doc_type,
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
                # Reset starts to current page
                chunk_page_start = page.page_number
                chunk_sec_start = page.page_number

            # When starting fresh chunk
            if not current_sentences:
                chunk_page_start = page.page_number
                chunk_sec_start = page.page_number
                current_section = page.section or ""
                current_source = page.source or current_source

            current_sentences.append(sentence)
            current_tokens += sent_tokens
            chunk_page_end = page.page_number
            chunk_sec_end = page.page_number
            if page.section:
                current_section = page.section

    # Flush remaining sentences
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        src_name = Path(current_source).name if current_source else "doc"
        chunks.append(Chunk(
            text=chunk_text,
            page_number=chunk_page_start,
            page_start=chunk_page_start,
            page_end=chunk_page_end,
            section=current_section,
            section_start=chunk_sec_start,
            section_end=chunk_sec_end,
            source=current_source,
            chunk_index=chunk_index,
            chunk_id=f"{src_name}_chunk_{chunk_index}",
            doc_type=document.doc_type,
        ))

    log.debug("Chunked document '%s' into %d chunks (size=%d, overlap=%d)",
              document.title, len(chunks), chunk_size, chunk_overlap)
    return chunks
