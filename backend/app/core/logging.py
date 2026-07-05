"""Structured logging. In GCP, logs flow to Cloud Logging via the
google-cloud-logging handler; locally we emit JSON lines to stdout."""
import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    if not settings.DEMO_MODE:
        try:
            from google.cloud import logging as gcp_logging

            client = gcp_logging.Client(project=settings.GCP_PROJECT_ID)
            client.setup_logging(log_level=logging.INFO)
        except Exception:  # fall back to stdout if ADC unavailable
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


def get_logger(name: str):
    return structlog.get_logger(name)
