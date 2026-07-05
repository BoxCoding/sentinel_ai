"""Cloud Function (2nd gen, Pub/Sub trigger on sentinel-alerts).

Fires when a decision cycle publishes an alert. If flood risk exceeds the
auto-alert threshold, escalates: writes an EMERGENCY alert doc, calls the
backend workflow endpoint, and logs to Cloud Logging.
"""
import base64
import json
import os

import functions_framework
import requests
from google.cloud import firestore, logging as gcp_logging

BACKEND_URL = os.environ.get("BACKEND_URL", "https://sentinel-backend-run-url")
FLOOD_THRESHOLD = float(os.environ.get("FLOOD_AUTO_ALERT_THRESHOLD", "0.90"))

log_client = gcp_logging.Client()
logger = log_client.logger("sentinel-alert-trigger")


@functions_framework.cloud_event
def on_alert(cloud_event):
    payload = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    risk = payload.get("risk_score") or 0.0
    logger.log_struct({"event": "alert_received", **payload}, severity="INFO")

    if risk >= FLOOD_THRESHOLD:
        db = firestore.Client()
        db.collection("alerts").add({
            "level": "EMERGENCY", "risk_score": risk,
            "cycle_id": payload.get("cycle_id"),
            "auto_escalated": True,
        })
        try:
            requests.post(f"{BACKEND_URL}/api/v1/agents/decision-cycle", timeout=30)
        except requests.RequestException as exc:
            logger.log_struct({"event": "escalation_callback_failed",
                               "error": str(exc)}, severity="ERROR")
        logger.log_struct({"event": "auto_escalated", "risk_score": risk},
                          severity="CRITICAL")
