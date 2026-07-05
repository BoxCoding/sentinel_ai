"""Cloud Monitoring custom metrics: decision-cycle risk score and agent
latency, so ops can alert on `custom.googleapis.com/sentinel/risk_score`."""
import time

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def record_metric(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    if settings.DEMO_MODE:
        log.info("metric", name=name, value=value, **(labels or {}))
        return
    try:
        from google.cloud import monitoring_v3

        client = monitoring_v3.MetricServiceClient()
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/sentinel/{name}"
        for k, v in (labels or {}).items():
            series.metric.labels[k] = v
        series.resource.type = "global"
        now = time.time()
        point = monitoring_v3.Point({
            "interval": {"end_time": {"seconds": int(now)}},
            "value": {"double_value": value},
        })
        series.points = [point]
        client.create_time_series(
            name=f"projects/{settings.GCP_PROJECT_ID}", time_series=[series]
        )
    except Exception as exc:
        log.warning("metric_write_failed", name=name, error=str(exc))
