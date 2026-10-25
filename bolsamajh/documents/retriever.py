"""Document retriever — long-context multilingual embeddings + FAISS vector search.

Adheres to Tier 2 Requirement 12:
- Replaces 128-token MiniLM with long-context multilingual embedder (intfloat/multilingual-e5-base / small, 512 max_seq_length).
- Applies correct 'passage: ' and 'query: ' prefixes required by E5 models.
- Calibrated cosine similarity refusal threshold based on empirical retrieval evaluation.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional

import numpy as np

from bolsamajh.documents.loader import Document
from bolsamajh.documents.chunker import Chunk, chunk_document

log = logging.getLogger(__name__)


class DocumentRetriever:
    """Embeds document chunks and retrieves relevant ones via FAISS.

    Uses long-context multilingual sentence-transformers (intfloat/multilingual-e5-base)
    with proper passage/query conditioning and cosine similarity scoring.
    """

    def __init__(
        self,
        embedding_model: str = "intfloat/multilingual-e5-base",
        chunk_size: int = 380,
        chunk_overlap: int = 40,
        refusal_threshold: float = 0.76,
    ):
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.refusal_threshold = refusal_threshold
        self._model = None
        self._index = None
        self._chunks: List[Chunk] = []
        self._document: Optional[Document] = None

    @property
    def is_loaded(self) -> bool:
        return self._index is not None and len(self._chunks) > 0

    @property
    def document_title(self) -> str:
        return self._document.title if self._document else ""

    def _load_embedding_model(self):
        """Lazy-load the sentence-transformer model with fallback."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        log.info("Loading embedding model: %s", self.embedding_model_name)
        t0 = time.time()
        try:
            self._model = SentenceTransformer(self.embedding_model_name)
        except Exception as e:
            log.warning("Failed to load %s (%s); falling back to multilingual-e5-small", self.embedding_model_name, e)
            self.embedding_model_name = "intfloat/multilingual-e5-small"
            self._model = SentenceTransformer("intfloat/multilingual-e5-small")

        log.info("Embedding model loaded in %.1fs (max_seq_length=%d)",
                 time.time() - t0, getattr(self._model, "max_seq_length", 512))

    def _prepare_text_for_embedding(self, text: str, is_query: bool = False) -> str:
        """Apply model-specific prefixes (e.g. E5 requires 'passage: ' and 'query: ')."""
        if "e5" in self.embedding_model_name.lower():
            prefix = "query: " if is_query else "passage: "
            return f"{prefix}{text.strip()}"
        return text.strip()

    def index_document(self, document: Document) -> int:
        """Index a document for retrieval.

        Returns:
            Number of chunks indexed.
        """
        import faiss

        self._load_embedding_model()
        self._document = document

        # Chunk the document with cross-page merging
        self._chunks = chunk_document(
            document,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        if not self._chunks:
            log.warning("No chunks generated from document")
            return 0

        # Generate embeddings with 'passage: ' prefix for E5
        log.info("Generating embeddings for %d chunks…", len(self._chunks))
        t0 = time.time()
        texts = [self._prepare_text_for_embedding(c.text, is_query=False) for c in self._chunks]
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        log.info("Embeddings generated in %.1fs", time.time() - t0)

        # Build FAISS inner-product index (cosine similarity for normalized vectors)
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings.astype(np.float32))

        log.info("FAISS index built: %d vectors, dim=%d", len(self._chunks), dim)
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 5, apply_threshold: bool = True) -> List[Chunk]:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: The search query (Hindi, English, or Hinglish).
            top_k: Number of results to return.
            apply_threshold: If True, filters out chunks below refusal_threshold.

        Returns:
            List of Chunk objects sorted by relevance.
        """
        if not self.is_loaded:
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
        k = min(top_k, len(self._chunks))
        scores, indices = self._index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                score_val = float(score)
                # Check refusal threshold
                if apply_threshold and score_val < self.refusal_threshold:
                    log.debug("Chunk %d score %.3f below refusal threshold %.2f; excluded",
                              idx, score_val, self.refusal_threshold)
                    continue

                c = self._chunks[idx]
                chunk = Chunk(
                    text=c.text,
                    page_number=c.page_number,
                    section=c.section,
                    source=c.source,
                    chunk_index=c.chunk_index,
                    score=score_val,
                )
                log.debug("  Score=%.3f  %s: %s…", score_val, chunk.citation, chunk.text[:60])
                results.append(chunk)

        log.info("Retrieved %d relevant chunks for query: %s", len(results), query[:50])
        return results

    def clear(self) -> None:
        """Clear the index and free memory."""
        self._index = None
        self._chunks = []
        self._document = None
        log.info("Document index cleared")
