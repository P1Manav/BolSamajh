"""Document chunker — sentence-aware chunking with cross-page merging and format-specific citations."""

import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Any

from bolsamajh.documents.loader import Document
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
        """Human-readable citation string conforming strictly to document type.

        - PDFs: 'Page X' or 'Pages X–Y' for merged cross-page chunks (never 'Section').
        - DOCX, Web, TXT, MD: 'Section X' or 'Sections X–Y' or 'Section: Title' (never 'Page').
        """
        # Strict document type check: rely on doc_type or exact .pdf file extension,
        # never loose substring matching.
        is_pdf = (
            self.doc_type.lower() == "pdf" or
            (not self.doc_type and self.source.lower().endswith(".pdf"))
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
        if self.section_start and self.section_end and self.section_start != self.section_end:
            return f"Sections {self.section_start}–{self.section_end}"
        if self.section:
            if not self.section.lower().startswith("section"):
                return f"Section: {self.section}"
            return self.section
        elif self.section_start:
            return f"Section {self.section_start}"
        return f"Section {self.chunk_index + 1}"


def count_tokens(text: str, tokenizer: Optional[Any] = None) -> int:
    """Count tokens using tokenizer if available, falling back to script-aware estimation.

    For Indic scripts (Devanagari, Gujarati), subword tokenization generates >= 3 tokens per word.
    For Latin text, ~1.3 tokens per word.
    """
    if not text or not text.strip():
        return 0

    if tokenizer is not None:
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception:
            pass

    tokens = 0
    for word in text.split():
        if re.search(r"[\u0900-\u097F\u0A80-\u0AFF]", word):
            # Devanagari or Gujarati word: conservative factor >= 3 tokens per word
            tokens += max(3, int(len(word) * 0.8))
        else:
            tokens += max(1, int(len(word) * 0.35 + 0.5))
    return max(1, tokens)


def _split_oversized_sentence(sentence: str, max_tokens: int, tokenizer: Optional[Any] = None) -> List[str]:
    """Split an unpunctuated or oversized sentence into segments fitting within max_tokens."""
    tok_count = count_tokens(sentence, tokenizer)
    if tok_count <= max_tokens:
        return [sentence]

    # Attempt to split on secondary punctuation first (commas, semicolons, dashes)
    delimiters = [",", ";", ":", " - ", "—"]
    for delim in delimiters:
        if delim in sentence:
            parts = sentence.split(delim)
            result = []
            cur_part = ""
            for p in parts:
                candidate = (cur_part + delim + p).strip() if cur_part else p.strip()
                if count_tokens(candidate, tokenizer) <= max_tokens:
                    cur_part = candidate
                else:
                    if cur_part:
                        result.append(cur_part)
                    cur_part = p.strip()
            if cur_part:
                result.append(cur_part)
            if all(count_tokens(r, tokenizer) <= max_tokens for r in result):
                return result

    # Fallback: split on whitespace words
    words = sentence.split()
    segments = []
    cur_words = []
    for w in words:
        cand = " ".join(cur_words + [w])
        if count_tokens(cand, tokenizer) > max_tokens and cur_words:
            segments.append(" ".join(cur_words))
            cur_words = [w]
        else:
            cur_words.append(w)
    if cur_words:
        segments.append(" ".join(cur_words))
    return segments or [sentence]


def chunk_document(
    document: Document,
    chunk_size: int = 380,
    chunk_overlap: int = 40,
    tokenizer: Optional[Any] = None,
) -> List[Chunk]:
    """Split a document into cross-page merged chunks aligned with 512-token embedders.

    Preserves sentence boundaries, splits oversized sentences, tracks accurate page spans
    across overlaps, and uses format-specific citations.
    """
    chunks: List[Chunk] = []
    chunk_index = 0

    # Each item: (sentence_text, page_number, section_name, source_path)
    current_items: List[tuple[str, int, str, str]] = []
    current_tokens = 0
    default_source = document.source

    for page in document.pages:
        raw_sentences = split_sentences(page.text)
        if not raw_sentences:
            continue

        for raw_sentence in raw_sentences:
            sub_sentences = _split_oversized_sentence(raw_sentence, chunk_size, tokenizer)
            for sentence in sub_sentences:
                sent_tokens = count_tokens(sentence, tokenizer)

                # If adding this sentence exceeds chunk_size, flush accumulated chunk
                if current_tokens + sent_tokens > chunk_size and current_items:
                    chunk_text = " ".join(item[0] for item in current_items)
                    page_start = current_items[0][1]
                    page_end = current_items[-1][1]
                    sec_name = current_items[0][2]
                    src = current_items[0][3] or default_source
                    src_name = Path(src).name if src else "doc"

                    chunks.append(Chunk(
                        text=chunk_text,
                        page_number=page_start,
                        page_start=page_start,
                        page_end=page_end,
                        section=sec_name,
                        section_start=page_start,
                        section_end=page_end,
                        source=src,
                        chunk_index=chunk_index,
                        chunk_id=f"{src_name}_chunk_{chunk_index}",
                        doc_type=document.doc_type,
                    ))
                    chunk_index += 1

                    # Overlap: preserve trailing items whose tokens sum to <= chunk_overlap
                    overlap_items: List[tuple[str, int, str, str]] = []
                    overlap_tokens = 0
                    for item in reversed(current_items):
                        toks = count_tokens(item[0], tokenizer)
                        if overlap_tokens + toks > chunk_overlap and overlap_items:
                            break
                        overlap_items.insert(0, item)
                        overlap_tokens += toks

                    current_items = overlap_items
                    current_tokens = overlap_tokens

                current_items.append((sentence, page.page_number, page.section or "", page.source or default_source))
                current_tokens += sent_tokens

    # Flush final remaining sentences
    if current_items:
        chunk_text = " ".join(item[0] for item in current_items)
        page_start = current_items[0][1]
        page_end = current_items[-1][1]
        sec_name = current_items[0][2]
        src = current_items[0][3] or default_source
        src_name = Path(src).name if src else "doc"

        chunks.append(Chunk(
            text=chunk_text,
            page_number=page_start,
            page_start=page_start,
            page_end=page_end,
            section=sec_name,
            section_start=page_start,
            section_end=page_end,
            source=src,
            chunk_index=chunk_index,
            chunk_id=f"{src_name}_chunk_{chunk_index}",
            doc_type=document.doc_type,
        ))

    log.debug("Chunked document '%s' into %d chunks (size=%d, overlap=%d)",
              document.title, len(chunks), chunk_size, chunk_overlap)
    return chunks
