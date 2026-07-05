"""Pub/Sub event bus. Incidents, alerts and workflow triggers flow through
topics so Cloud Functions / Cloud Run subscribers can react asynchronously.
Demo mode dispatches to in-process subscribers synchronously."""
import json
from collections import defaultdict
from typing import Callable

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_demo_subscribers: dict[str, list[Callable[[dict], None]]] = defaultdict(list)


class PubSubService:
    def __init__(self):
        self._publisher = None

    def _pub(self):
        if self._publisher is None:
            from google.cloud import pubsub_v1

            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    def publish(self, topic: str, message: dict) -> None:
        log.info("pubsub_publish", topic=topic, keys=list(message.keys()))
        if settings.DEMO_MODE:
            for handler in _demo_subscribers.get(topic, []):
                try:
                    handler(message)
                except Exception as exc:
                    log.error("demo_subscriber_error", topic=topic, error=str(exc))
            return
        path = self._pub().topic_path(settings.GCP_PROJECT_ID, topic)
        self._pub().publish(path, json.dumps(message, default=str).encode())

    def subscribe_local(self, topic: str, handler: Callable[[dict], None]) -> None:
        """Register an in-process handler (demo mode only; prod uses push subscriptions)."""
        _demo_subscribers[topic].append(handler)


pubsub = PubSubService()
