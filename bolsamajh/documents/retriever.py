"""Document retriever — long-context multilingual embeddings + FAISS vector search.

Adheres to Tier 2 Requirement 12:
- Replaces 128-token MiniLM with long-context multilingual embedder (intfloat/multilingual-e5-base / small, 512 max_seq_length).
- Applies correct 'passage: ' and 'query: ' prefixes required by E5 models.
- Calibrated cosine similarity refusal threshold based on empirical retrieval evaluation.
- Thread-safe atomic index swapping via threading.Lock.
- Scaled refusal thresholds per embedding model with loud warnings on fallback.
"""

import logging
import time
import threading
from typing import List, Optional

import numpy as np

from bolsamajh.documents.loader import Document
from bolsamajh.documents.chunker import Chunk, chunk_document

log = logging.getLogger(__name__)

# Calibrated refusal thresholds per embedding model
MODEL_THRESHOLDS = {
    "intfloat/multilingual-e5-base": 0.785,
    "intfloat/multilingual-e5-small": 0.760,
    "sentence-transformers/paraphrase-multilingual-minilm-l12-v2": 0.720,
}


class DocumentRetriever:
    """Embeds document chunks and retrieves relevant ones via FAISS.

    Uses long-context multilingual sentence-transformers (intfloat/multilingual-e5-base)
    with proper passage/query conditioning, cosine similarity scoring, and thread-safe atomic swapping.
    """

    def __init__(
        self,
        embedding_model: str = "intfloat/multilingual-e5-base",
        chunk_size: int = 380,
        chunk_overlap: int = 40,
        refusal_threshold: float = 0.785,
    ):
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.refusal_threshold = refusal_threshold
        self._lock = threading.Lock()
        self._model = None
        self._tokenizer = None
        self._index = None
        self._chunks: List[Chunk] = []
        self._document: Optional[Document] = None

    @property
    def is_loaded(self) -> bool:
        with self._lock:
            return self._index is not None and len(self._chunks) > 0

    @property
    def document_title(self) -> str:
        with self._lock:
            return self._document.title if self._document else ""

    def clear(self) -> None:
        """Clear currently indexed document and FAISS index under lock."""
        with self._lock:
            self._index = None
            self._chunks = []
            self._document = None

    def _load_embedding_model(self):
        """Lazy-load the sentence-transformer model with fallback and threshold scaling."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        log.info("Loading embedding model: %s", self.embedding_model_name)
        t0 = time.time()
        try:
            self._model = SentenceTransformer(self.embedding_model_name)
            self._tokenizer = getattr(self._model, "tokenizer", None)
        except Exception as e:
            prev_thresh = self.refusal_threshold
            fallback_model = "intfloat/multilingual-e5-small"
            new_thresh = MODEL_THRESHOLDS.get(fallback_model, 0.760)
            log.warning(
                "CRITICAL WARNING: Failed to load '%s' (%s). Falling back to '%s'. "
                "Scaling refusal threshold from %.3f to %.3f. High-precision retrieval may be degraded.",
                self.embedding_model_name, e, fallback_model, prev_thresh, new_thresh
            )
            self.embedding_model_name = fallback_model
            self.refusal_threshold = new_thresh
            self._model = SentenceTransformer(fallback_model)
            self._tokenizer = getattr(self._model, "tokenizer", None)

        log.info("Embedding model loaded in %.1fs (max_seq_length=%d, threshold=%.3f)",
                 time.time() - t0, getattr(self._model, "max_seq_length", 512), self.refusal_threshold)

    def _prepare_text_for_embedding(self, text: str, is_query: bool = False) -> str:
        """Apply model-specific prefixes (e.g. E5 requires 'passage: ' and 'query: ')."""
        if "e5" in self.embedding_model_name.lower():
            prefix = "query: " if is_query else "passage: "
            return f"{prefix}{text.strip()}"
        return text.strip()

    def index_document(self, document: Document) -> int:
        """Index a document for retrieval.

        Builds the entire chunk list, embeddings, and FAISS index completely before
        swapping them atomically under a thread lock.

        Returns:
            Number of chunks indexed.
        """
        import faiss

        self._load_embedding_model()

        # 1. Chunk the document with tokenizer-aware sizing and cross-page merging
        new_chunks = chunk_document(
            document,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            tokenizer=self._tokenizer,
        )

        if not new_chunks:
            log.warning("No chunks generated from document '%s'", document.title)
            with self._lock:
                self._index = None
                self._chunks = []
                self._document = None
            return 0

        # 2. Generate embeddings with 'passage: ' prefix for E5
        log.info("Generating embeddings for %d chunks…", len(new_chunks))
        t0 = time.time()
        texts = [self._prepare_text_for_embedding(c.text, is_query=False) for c in new_chunks]
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        log.info("Embeddings generated in %.1fs", time.time() - t0)

        # 3. Build new FAISS inner-product index
        dim = embeddings.shape[1]
        new_index = faiss.IndexFlatIP(dim)
        new_index.add(embeddings.astype(np.float32))

        # 4. Atomically swap new index, chunks, and document together
        with self._lock:
            self._index = new_index
            self._chunks = new_chunks
            self._document = document

        log.info("FAISS index built and atomically swapped: %d vectors, dim=%d", len(new_chunks), dim)
        return len(new_chunks)

    def retrieve(self, query: str, top_k: int = 5, apply_threshold: bool = True) -> List[Chunk]:
        """Retrieve the most relevant chunks for a query.

        Thread-safe: snapshots index and chunks under lock.
        """
        with self._lock:
            index = self._index
            chunks = list(self._chunks)
            threshold = self.refusal_threshold

        if index is None or not chunks:
            log.warning("No document indexed")
            return []

        self._load_embedding_model()

        # Encode query with 'query: ' prefix for E5
        query_text = self._prepare_text_for_embedding(query, is_query=True)
        query_vec = self._model.encode(
            [query_text],
            normalize_embeddings=True,
        ).astype(np.float32)

        # Search index
        k = min(top_k, len(chunks))
        scores, indices = index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(chunks):
                score_val = float(score)
                # Check refusal threshold
                if apply_threshold and score_val < threshold:
                    log.debug("Chunk %d score %.3f below refusal threshold %.3f; excluded",
                              idx, score_val, threshold)
                    continue

                c = chunks[idx]
                chunk = Chunk(
                    text=c.text,
                    page_number=c.page_number,
                    page_start=c.page_start,
                    page_end=c.page_end,
                    section=c.section,
                    section_start=c.section_start,
                    section_end=c.section_end,
                    source=c.source,
                    chunk_index=c.chunk_index,
                    chunk_id=c.chunk_id,
                    score=score_val,
                    doc_type=c.doc_type,
                )
                log.debug("  Score=%.3f  %s: %s…", score_val, chunk.citation, chunk.text[:60])
                results.append(chunk)

        log.info("Retrieved %d relevant chunks for query: %s", len(results), query[:50])
        return results

    def clear(self) -> None:
        """Clear the index and free memory atomically."""
        with self._lock:
            self._index = None
            self._chunks = []
            self._document = None
        log.info("Document index cleared")
