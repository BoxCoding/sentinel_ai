"""Live weather feed: Open-Meteo (free, no API key) for all districts in one
batched request. Real observations: temperature, humidity, wind, 6-hour
rainfall, topsoil moisture. Derived: river level (baseline + rainfall
response) and drainage capacity (static infrastructure data from geography).

Cached for 10 minutes; falls back to the synthetic CSV on any failure so the
platform never goes dark offline.
"""
import time

import httpx
import pandas as pd

from app.core.geography import DISTRICT_META
from app.core.logging import get_logger

log = get_logger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_S = 600

_cache: dict = {"ts": 0.0, "df": None}


def fetch_live_weather() -> pd.DataFrame | None:
    """Return the live weather table, or None if the feed is unreachable."""
    if _cache["df"] is not None and time.time() - _cache["ts"] < CACHE_TTL_S:
        return _cache["df"]

    districts = list(DISTRICT_META.items())
    params = {
        "latitude": ",".join(str(m["lat"]) for _, m in districts),
        "longitude": ",".join(str(m["lng"]) for _, m in districts),
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "hourly": "precipitation,soil_moisture_0_to_1cm",
        "past_hours": 6,
        "forecast_hours": 1,
        "timezone": "UTC",
    }
    try:
        resp = httpx.get(OPEN_METEO_URL, params=params, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        log.warning("open_meteo_unavailable", error=str(exc))
        return None

    # single-location responses are a dict, multi-location a list
    locations = payload if isinstance(payload, list) else [payload]
    if len(locations) != len(districts):
        log.warning("open_meteo_shape_mismatch", got=len(locations))
        return None

    rows = []
    for (district, meta), loc in zip(districts, locations):
        current = loc.get("current", {})
        hourly = loc.get("hourly", {})
        rain_6h = float(sum(p or 0 for p in hourly.get("precipitation", [])[:6]))
        soil_values = [s for s in hourly.get("soil_moisture_0_to_1cm", []) if s is not None]
        # m3/m3 topsoil moisture: ~0.45 is saturated loam
        soil_saturation = min(max((soil_values[-1] / 0.45) if soil_values else 0.5, 0.05), 0.98)
        base_river = 3.2 if meta["flood_prone"] else 2.4
        rows.append({
            "district": district,
            "city": meta["city"],
            "lat": meta["lat"],
            "lng": meta["lng"],
            "elevation_m": meta["relative_elev_m"],
            "rain_6h_mm": round(rain_6h, 1),
            "river_level_m": round(min(base_river + rain_6h * 0.012, 5.5), 2),
            "drainage_capacity": meta["drainage"],
            "soil_saturation": round(soil_saturation, 2),
            "temp_c": float(current.get("temperature_2m") or 28.0),
            "humidity": round(float(current.get("relative_humidity_2m") or 60) / 100, 2),
            "wind_kmh": float(current.get("wind_speed_10m") or 8.0),
        })

    df = pd.DataFrame(rows)
    _cache.update(ts=time.time(), df=df)
    log.info("open_meteo_refreshed", districts=len(df),
             max_rain_6h=float(df["rain_6h_mm"].max()))
    return df
