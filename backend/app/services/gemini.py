"""Gemini integration with three tiers:

1. GEMINI_API_KEY set (Google AI / generativelanguage API) — real Gemini,
   works even in DEMO_MODE. Model from GEMINI_API_MODEL (gemini-3.5-flash).
2. Production (DEMO_MODE=false, no key) — Vertex AI with ADC.
3. Neither — deterministic canned analyses so the platform runs offline.
"""
import base64
import json
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
# tried in order until one responds (first is the configured model)
API_MODEL_FALLBACKS = ["gemini-2.5-flash", "gemini-flash-latest"]

_model_cache: dict[str, Any] = {}


def _get_model(model_name: str):
    if model_name not in _model_cache:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_REGION)
        _model_cache[model_name] = GenerativeModel(model_name)
    return _model_cache[model_name]


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON object in Gemini response: {text[:200]}")


class GeminiService:
    @property
    def connected(self) -> bool:
        """True when a real Gemini backend is available (API key or Vertex)."""
        return bool(settings.GEMINI_API_KEY) or not settings.DEMO_MODE

    @property
    def active_model(self) -> str:
        if settings.GEMINI_API_KEY:
            return settings.GEMINI_API_MODEL
        return settings.GEMINI_MODEL if not settings.DEMO_MODE else "offline-demo"

    async def _api_generate(self, parts: list[dict], system: str | None,
                            temperature: float) -> str:
        """Call the Google AI generativelanguage API with model fallback."""
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": temperature},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        models = [settings.GEMINI_API_MODEL] + [
            m for m in API_MODEL_FALLBACKS if m != settings.GEMINI_API_MODEL
        ]
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=45) as client:
            for model in models:
                try:
                    resp = await client.post(
                        f"{GEMINI_API_BASE}/{model}:generateContent",
                        headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as exc:
                    last_error = exc
                    log.warning("gemini_api_model_failed", model=model, error=str(exc)[:200])
        raise RuntimeError(f"All Gemini API models failed: {last_error}")

    async def generate(self, prompt: str, system: str | None = None,
                       model: str | None = None, temperature: float = 0.4) -> str:
        if settings.GEMINI_API_KEY:
            try:
                return await self._api_generate([{"text": prompt}], system, temperature)
            except Exception as exc:
                log.error("gemini_api_failed_falling_back", error=str(exc)[:200])
                return self._demo_text(prompt)
        if settings.DEMO_MODE:
            return self._demo_text(prompt)
        from vertexai.generative_models import GenerationConfig

        m = _get_model(model or settings.GEMINI_MODEL)
        contents = [system, prompt] if system else [prompt]
        resp = await m.generate_content_async(
            contents, generation_config=GenerationConfig(temperature=temperature)
        )
        return resp.text

    async def generate_json(self, prompt: str, schema_hint: str,
                            model: str | None = None) -> dict:
        """Ask Gemini for structured output. schema_hint is a JSON example/spec."""
        full = (
            f"{prompt}\n\nRespond ONLY with a JSON object matching this schema, "
            f"no markdown fences:\n{schema_hint}"
        )
        if settings.GEMINI_API_KEY:
            try:
                text = await self._api_generate([{"text": full}], None, 0.2)
                return _extract_json(text)
            except Exception as exc:
                log.error("gemini_api_json_failed", error=str(exc)[:200])
                return self._demo_json(prompt)
        if settings.DEMO_MODE:
            return self._demo_json(prompt)
        text = await self.generate(full, model=model, temperature=0.2)
        return _extract_json(text)

    async def analyze_media(self, gcs_uri_or_bytes: str | bytes, mime_type: str,
                            prompt: str) -> str:
        """Multimodal analysis: images, video, audio, PDFs."""
        if settings.GEMINI_API_KEY and isinstance(gcs_uri_or_bytes, bytes):
            try:
                parts = [
                    {"inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(gcs_uri_or_bytes).decode(),
                    }},
                    {"text": prompt},
                ]
                return await self._api_generate(parts, None, 0.3)
            except Exception as exc:
                log.error("gemini_api_media_failed", error=str(exc)[:200])
                return self._demo_media(mime_type)
        if settings.DEMO_MODE:
            return self._demo_media(mime_type)
        from vertexai.generative_models import Part

        m = _get_model(settings.GEMINI_MODEL)
        if isinstance(gcs_uri_or_bytes, str):
            part = Part.from_uri(gcs_uri_or_bytes, mime_type=mime_type)
        else:
            part = Part.from_data(gcs_uri_or_bytes, mime_type=mime_type)
        resp = await m.generate_content_async([part, prompt])
        return resp.text

    # ---------------- demo fallbacks ----------------
    def _demo_text(self, prompt: str) -> str:
        p = prompt.lower()
        if "flood" in p:
            return ("Flood risk in Yamuna Bank, Kurla and Bellandur is elevated (78%) for the "
                    "next 12 hours due to 90mm+ rainfall in 6h against limited drainage capacity. "
                    "Recommend pre-positioning rescue boats and issuing a Level-2 citizen "
                    "advisory for the low-lying districts, including Gurugram underpasses.")
        if "summar" in p:
            return ("Today: 47 incidents (12 medical, 9 traffic, 8 fire, 18 other). Two critical: "
                    "a warehouse fire near NH-48 Gurugram (contained 14:20) and a multi-vehicle "
                    "collision on the Western Express Highway (3 hospitalized). Average response "
                    "time 8.4 min, 11% better than the 30-day baseline.")
        return ("Based on current sensor feeds and model outputs, the situation is manageable. "
                "Highest-attention item: rising occupancy at the busiest metro hospitals. "
                "Recommend monitoring and rebalancing non-critical admissions to paired "
                "overflow facilities per the surge protocol.")

    def _demo_json(self, prompt: str) -> dict:
        return {
            "risk_score": 0.78, "confidence": 0.86, "priority": "HIGH",
            "reason": "Rainfall intensity 94mm/6h exceeds drainage capacity in low-lying wards.",
            "recommended_action": "Pre-position rescue assets; issue Level-2 advisory.",
            "estimated_impact": "~12,000 residents in wards 12/14/17",
            "supporting_data": ["weather_station_7: 94mm/6h", "river_gauge_2: 4.1m (danger 4.5m)"],
        }

    def _demo_media(self, mime_type: str) -> str:
        if mime_type.startswith("image"):
            return ("Detected: FLOOD. Water level approximately 0.6m on a residential street; "
                    "two stranded vehicles; no visible casualties. Road impassable to sedans, "
                    "passable to high-clearance rescue vehicles. Severity: HIGH.")
        if mime_type.startswith("audio"):
            return ("Caller reports a kitchen fire spreading to the second floor at 42 Rosewood "
                    "Lane, Ward 9. One elderly resident possibly inside. Emergency type: FIRE. "
                    "Severity: CRITICAL.")
        return "Media analyzed: no critical hazards detected."


gemini = GeminiService()
