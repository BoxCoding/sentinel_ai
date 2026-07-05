"""Cloud Function (Pub/Sub trigger on sentinel-incidents).

Streams every new incident into BigQuery for analytics/Looker and stamps the
Firestore doc with the warehouse insert time.
"""
import base64
import json
import os
from datetime import datetime, timezone

import functions_framework
from google.cloud import bigquery, firestore

PROJECT = os.environ.get("GCP_PROJECT_ID", "sentinel-ai-hackathon")
TABLE = f"{PROJECT}.sentinel_ai.incidents_stream"


@functions_framework.cloud_event
def on_incident(cloud_event):
    incident = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    bq = bigquery.Client(project=PROJECT)
    row = {
        "incident_id": incident.get("incident_id"),
        "type": incident.get("type") or incident.get("emergency_type"),
        "district": incident.get("district"),
        "source": incident.get("source", "unknown"),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    errors = bq.insert_rows_json(TABLE, [row])
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    if incident_id := incident.get("incident_id"):
        firestore.Client().collection("incidents").document(incident_id).set(
            {"warehoused_at": row["ingested_at"]}, merge=True)
