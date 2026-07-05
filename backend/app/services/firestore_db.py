"""Firestore for real-time operational state (incidents, alerts, agent runs,
notifications). Demo mode keeps collections in process memory."""
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

_demo_store: dict[str, dict[str, dict]] = {}


class FirestoreService:
    def __init__(self):
        self._client = None

    def _db(self):
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(
                project=settings.GCP_PROJECT_ID, database=settings.FIRESTORE_DATABASE
            )
        return self._client

    def add(self, collection: str, data: dict, doc_id: str | None = None) -> str:
        doc_id = doc_id or uuid.uuid4().hex[:12]
        data = {**data, "created_at": datetime.now(timezone.utc).isoformat()}
        if settings.DEMO_MODE:
            _demo_store.setdefault(collection, {})[doc_id] = data
        else:
            self._db().collection(collection).document(doc_id).set(data)
        return doc_id

    def get(self, collection: str, doc_id: str) -> dict | None:
        if settings.DEMO_MODE:
            return _demo_store.get(collection, {}).get(doc_id)
        snap = self._db().collection(collection).document(doc_id).get()
        return snap.to_dict() if snap.exists else None

    def update(self, collection: str, doc_id: str, data: dict) -> None:
        if settings.DEMO_MODE:
            _demo_store.setdefault(collection, {}).setdefault(doc_id, {}).update(data)
        else:
            self._db().collection(collection).document(doc_id).update(data)

    def list(self, collection: str, limit: int = 100,
             order_by: str = "created_at", descending: bool = True) -> list[dict]:
        if settings.DEMO_MODE:
            docs = [{"id": k, **v} for k, v in _demo_store.get(collection, {}).items()]
            docs.sort(key=lambda d: d.get(order_by, ""), reverse=descending)
            return docs[:limit]
        from google.cloud import firestore

        direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
        query = self._db().collection(collection).order_by(order_by, direction=direction).limit(limit)
        return [{"id": s.id, **s.to_dict()} for s in query.stream()]


fs = FirestoreService()
