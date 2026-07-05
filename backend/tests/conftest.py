"""Tests run fully offline and deterministic: disable the live weather feed
and the Gemini API key (env vars take precedence over backend/.env)."""
import os

os.environ["LIVE_WEATHER"] = "false"
os.environ["GEMINI_API_KEY"] = ""
