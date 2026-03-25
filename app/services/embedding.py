from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wraps embedding model initialization and encoding logic with lazy loading."""

    _KNOWN_DIMS = {
        "all-MiniLM-L6-v2": 384,
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", embedding_dim: int | None = None) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._lock = threading.Lock()
        self.dimension = embedding_dim or self._KNOWN_DIMS.get(model_name, 384)

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                # Import lazily so web service can bind port before heavy ML libs load.
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                # Align configured dimension with actual model dimension after lazy load.
                self.dimension = self._model.get_sentence_embedding_dimension()
        return self._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        model = self._ensure_model()
        vectors = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vectors.astype("float32")

    def embed_query(self, query: str) -> np.ndarray:
        vector = self.embed_texts([query])[0]
        return vector
