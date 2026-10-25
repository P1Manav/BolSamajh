"""Document retriever — multilingual embeddings + FAISS vector search."""

import logging
import time
from pathlib import Path

import numpy as np

from bolsamajh.documents.loader import Document
from bolsamajh.documents.chunker import Chunk, chunk_document

log = logging.getLogger(__name__)


class DocumentRetriever:
    """Embeds document chunks and retrieves relevant ones via FAISS.

    Uses sentence-transformers with a multilingual model for
    Hindi + English queries.
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._model = None
        self._index = None
        self._chunks: list[Chunk] = []
        self._document: Document | None = None

    @property
    def is_loaded(self) -> bool:
        return self._index is not None and len(self._chunks) > 0

    @property
    def document_title(self) -> str:
        return self._document.title if self._document else ""

    def _load_embedding_model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        log.info("Loading embedding model: %s", self.embedding_model_name)
        t0 = time.time()
        self._model = SentenceTransformer(self.embedding_model_name)
        log.info("Embedding model loaded in %.1fs", time.time() - t0)

    def index_document(self, document: Document) -> int:
        """Index a document for retrieval.

        Returns:
            Number of chunks indexed.
        """
        import faiss

        self._load_embedding_model()
        self._document = document

        # Chunk the document
        self._chunks = chunk_document(
            document,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        if not self._chunks:
            log.warning("No chunks generated from document")
            return 0

        # Generate embeddings
        log.info("Generating embeddings for %d chunks…", len(self._chunks))
        t0 = time.time()
        texts = [c.text for c in self._chunks]
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        log.info("Embeddings generated in %.1fs", time.time() - t0)

        # Build FAISS index
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # Inner product (cosine for normalized)
        self._index.add(embeddings.astype(np.float32))

        log.info("FAISS index built: %d vectors, dim=%d", len(self._chunks), dim)
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: The search query (can be Hindi, English, or Hinglish).
            top_k: Number of results to return.

        Returns:
            List of Chunk objects sorted by relevance.
        """
        if not self.is_loaded:
            log.warning("No document indexed")
            return []

        self._load_embedding_model()

        # Encode query
        query_vec = self._model.encode(
            [query],
            normalize_embeddings=True,
        ).astype(np.float32)

        # Search
        k = min(top_k, len(self._chunks))
        scores, indices = self._index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:  # FAISS returns -1 for missing
                c = self._chunks[idx]
                chunk = Chunk(
                    text=c.text,
                    page_number=c.page_number,
                    section=c.section,
                    source=c.source,
                    chunk_index=c.chunk_index,
                    score=float(score),
                )
                log.debug("  Score=%.3f  %s: %s…",
                          score, chunk.citation, chunk.text[:60])
                results.append(chunk)

        log.info("Retrieved %d chunks for query: %s", len(results), query[:50])
        return results


    def clear(self) -> None:
        """Clear the index and free memory."""
        self._index = None
        self._chunks = []
        self._document = None
        log.info("Document index cleared")
