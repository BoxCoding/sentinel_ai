"""Central configuration. All GCP resources are configurable via env vars;
DEMO_MODE=true runs the full platform against local mocks (no cloud creds needed)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env regardless of the process working directory
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # App
    APP_NAME: str = "Sentinel AI"
    ENV: str = "development"
    DEMO_MODE: bool = True  # true => mock GCP clients, deterministic synthetic data
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Auth
    JWT_SECRET: str = "change-me-in-secret-manager"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # GCP
    GCP_PROJECT_ID: str = "sentinel-ai-hackathon"
    GCP_REGION: str = "us-central1"
    GEMINI_MODEL: str = "gemini-2.5-pro"
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-005"

    # Gemini API (Google AI) — enables real AI even in DEMO_MODE
    GEMINI_API_KEY: str = ""
    GEMINI_API_MODEL: str = "gemini-3.5-flash"

    # Live data feeds (Open-Meteo needs no key)
    LIVE_WEATHER: bool = True

    # Vertex AI Vector Search
    VECTOR_INDEX_ID: str = ""
    VECTOR_INDEX_ENDPOINT_ID: str = ""
    VECTOR_DEPLOYED_INDEX_ID: str = "sentinel_kb_deployed"

    # Data stores
    BQ_DATASET: str = "sentinel_ai"
    GCS_BUCKET: str = "sentinel-ai-data"
    GCS_KB_BUCKET: str = "sentinel-ai-knowledge-base"
    FIRESTORE_DATABASE: str = "(default)"
    ALLOYDB_URI: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"

    # Pub/Sub topics
    TOPIC_INCIDENTS: str = "sentinel-incidents"
    TOPIC_ALERTS: str = "sentinel-alerts"
    TOPIC_WORKFLOWS: str = "sentinel-workflows"

    # External
    GOOGLE_MAPS_API_KEY: str = ""
    DOCAI_PROCESSOR_ID: str = ""

    # Thresholds
    FLOOD_AUTO_ALERT_THRESHOLD: float = 0.90
    CRITICAL_RISK_THRESHOLD: float = 0.75


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
