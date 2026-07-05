"""Vertex AI Vector Search wrapper with an in-memory fallback index.

Production: MatchingEngineIndexEndpoint.find_neighbors against the deployed
index. Demo: brute-force cosine over locally stored chunks (fine for <10k docs)."""
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings import embeddings

log = get_logger(__name__)


class VectorSearchService:
    def __init__(self):
        # local fallback store: id -> (vector, payload)
        self._local: dict[str, tuple[np.ndarray, dict]] = {}

    def upsert(self, doc_id: str, text: str, metadata: dict) -> None:
        vec = np.array(embeddings.embed([text])[0])
        self._local[doc_id] = (vec, {"text": text, **metadata})
        if not settings.DEMO_MODE and settings.VECTOR_INDEX_ID:
            from google.cloud import aiplatform

            aiplatform.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_REGION)
            index = aiplatform.MatchingEngineIndex(settings.VECTOR_INDEX_ID)
            index.upsert_datapoints(datapoints=[
                {"datapoint_id": doc_id, "feature_vector": vec.tolist()}
            ])

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        qvec = np.array(embeddings.embed([query], task="RETRIEVAL_QUERY")[0])
        if not settings.DEMO_MODE and settings.VECTOR_INDEX_ENDPOINT_ID:
            return self._remote_search(qvec, top_k)
        return self._local_search(qvec, top_k)

    def _local_search(self, qvec: np.ndarray, top_k: int) -> list[dict]:
        scored = []
        for doc_id, (vec, payload) in self._local.items():
            denom = np.linalg.norm(qvec) * np.linalg.norm(vec)
            sim = float(np.dot(qvec, vec) / denom) if denom else 0.0
            scored.append({"id": doc_id, "score": sim, **payload})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _remote_search(self, qvec: np.ndarray, top_k: int) -> list[dict]:
        from google.cloud import aiplatform

        aiplatform.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_REGION)
        endpoint = aiplatform.MatchingEngineIndexEndpoint(settings.VECTOR_INDEX_ENDPOINT_ID)
        resp = endpoint.find_neighbors(
            deployed_index_id=settings.VECTOR_DEPLOYED_INDEX_ID,
            queries=[qvec.tolist()], num_neighbors=top_k,
        )
        results = []
        for neighbor in resp[0]:
            payload = self._local.get(neighbor.id, (None, {"text": ""}))[1]
            results.append({"id": neighbor.id, "score": 1 - neighbor.distance, **payload})
        return results


vector_search = VectorSearchService()
