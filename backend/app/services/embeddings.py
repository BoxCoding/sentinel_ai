"""Vertex AI Embeddings (text-embedding-005). Demo mode uses a
deterministic hash-based embedding so vector search works offline."""
import hashlib

import numpy as np

from app.core.config import settings

_DIM = 768


class EmbeddingService:
    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is None:
            import vertexai
            from vertexai.language_models import TextEmbeddingModel

            vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_REGION)
            self._model = TextEmbeddingModel.from_pretrained(settings.EMBEDDING_MODEL)
        return self._model

    def embed(self, texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        if settings.DEMO_MODE:
            return [self._demo_embed(t) for t in texts]
        from vertexai.language_models import TextEmbeddingInput

        model = self._load()
        inputs = [TextEmbeddingInput(t, task) for t in texts]
        return [e.values for e in model.get_embeddings(inputs)]

    def _demo_embed(self, text: str) -> list[float]:
        # Deterministic pseudo-embedding: word-hash bag projected to _DIM.
        # Overlapping vocabulary => higher cosine similarity, good enough for demo retrieval.
        vec = np.zeros(_DIM)
        for word in text.lower().split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            rng = np.random.default_rng(h % (2**32))
            vec += rng.standard_normal(_DIM)
        norm = np.linalg.norm(vec)
        return (vec / norm if norm > 0 else vec).tolist()


embeddings = EmbeddingService()
