"""Cloud Storage for uploaded media and knowledge-base documents.
Demo mode writes to a local .demo_storage directory."""
from pathlib import Path

from app.core.config import settings

DEMO_STORAGE = Path(__file__).resolve().parents[3] / ".demo_storage"


class StorageService:
    def __init__(self):
        self._client = None

    def _gcs(self):
        if self._client is None:
            from google.cloud import storage

            self._client = storage.Client(project=settings.GCP_PROJECT_ID)
        return self._client

    def upload(self, data: bytes, path: str, bucket: str | None = None,
               content_type: str = "application/octet-stream") -> str:
        bucket = bucket or settings.GCS_BUCKET
        if settings.DEMO_MODE:
            try:
                local = DEMO_STORAGE / bucket / path
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(data)
            except OSError:  # read-only filesystem (serverless) -> /tmp
                import tempfile

                local = Path(tempfile.gettempdir()) / "sentinel_storage" / bucket / path
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(data)
            return f"gs://{bucket}/{path}"
        blob = self._gcs().bucket(bucket).blob(path)
        blob.upload_from_string(data, content_type=content_type)
        return f"gs://{bucket}/{path}"

    def download(self, gcs_uri: str) -> bytes:
        bucket, _, path = gcs_uri.removeprefix("gs://").partition("/")
        if settings.DEMO_MODE:
            return (DEMO_STORAGE / bucket / path).read_bytes()
        return self._gcs().bucket(bucket).blob(path).download_as_bytes()


storage = StorageService()
