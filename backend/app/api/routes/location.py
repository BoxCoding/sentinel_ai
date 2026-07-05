"""Location intelligence: the user's coordinates in, an AI situational
briefing out — nearest district, live weather, flood/fire/accident risks with
explanations, nearest hospitals, and prioritized safety suggestions.
Production composes the narrative with Gemini; demo mode builds it from the
same data deterministically."""
import math

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_user
from app.ml.predictors import engine
from app.services.bigquery_svc import bq
from app.services.gemini import gemini
from app.xai.explainer import explain_prediction

router = APIRouter(prefix="/location", tags=["location"])


class LocationRequest(BaseModel):
    lat: float
    lng: float


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _suggestions(flood: float, fire: float, accident: float,
                 weather: dict, hospitals: list[dict]) -> list[str]:
    tips: list[str] = []
    if flood > 0.75:
        tips.append("HIGH flood risk here — avoid underpasses and low-lying roads; "
                    "move vehicles to elevated parking now.")
    elif flood > 0.5:
        tips.append("Moderate flood risk — keep away from storm drains and riverbanks; "
                    "plan an elevated route home.")
    if weather.get("rain_6h_mm", 0) > 80:
        tips.append(f"Heavy rainfall ({weather['rain_6h_mm']}mm in 6h) — expect "
                    "waterlogged stretches and 30-50% longer travel times.")
    if fire > 0.6:
        tips.append("Elevated fire risk (heat/wind/low humidity) — report any smoke "
                    "immediately; avoid open flames outdoors.")
    if accident > 0.6:
        tips.append("Accident probability is high on nearby corridors — maintain "
                    "distance, avoid two-wheelers on flooded lanes.")
    surging = [h for h in hospitals if h["occupancy"] > 0.9]
    if surging:
        names = ", ".join(h["hospital"] for h in surging)
        alt = next((h["hospital"] for h in hospitals if h["occupancy"] <= 0.85), None)
        tips.append(f"{names} near you {'is' if len(surging) == 1 else 'are'} at surge "
                    f"capacity{f' — for non-critical care prefer {alt}' if alt else ''}.")
    if not tips:
        tips.append("Conditions near you are normal. Save the emergency helpline (112) "
                    "and keep location services on for targeted alerts.")
    return tips


@router.post("/briefing")
async def location_briefing(body: LocationRequest, _=Depends(get_current_user)):
    weather = bq.table("weather_current")
    if weather.empty:
        raise HTTPException(status_code=503, detail="No weather telemetry available")

    weather["distance_km"] = weather.apply(
        lambda r: _haversine_km(body.lat, body.lng, r["lat"], r["lng"]), axis=1)
    near = weather.nsmallest(1, "distance_km").iloc[0]

    flood_p, flood_model, flood_X = engine.flood_probability({
        "rain_6h_mm": near["rain_6h_mm"], "river_level_m": near["river_level_m"],
        "drainage_capacity": near["drainage_capacity"],
        "soil_saturation": near["soil_saturation"], "elevation_m": near["elevation_m"],
    })
    fire_p, _, _ = engine.fire_risk({
        "temp_c": near["temp_c"], "humidity": near["humidity"],
        "wind_kmh": near["wind_kmh"], "building_age": 35, "industrial": 0,
    })
    accident_p, _, _ = engine.accident_probability({
        "congestion": 0.6, "rain_mm": near["rain_6h_mm"] / 6,
        "hour": 18, "is_night": 0, "road_quality": 0.7,
    })

    hospitals_df = bq.table("hospital_status")
    hospitals: list[dict] = []
    if not hospitals_df.empty:
        hospitals_df["distance_km"] = hospitals_df.apply(
            lambda r: _haversine_km(body.lat, body.lng, r["lat"], r["lng"]), axis=1)
        hospitals = (hospitals_df.nsmallest(3, "distance_km")
                     .assign(distance_km=lambda d: d["distance_km"].round(1))
                     .to_dict("records"))

    tips = _suggestions(flood_p, fire_p, accident_p, near.to_dict(), hospitals)

    if not gemini.connected:
        summary = (
            f"You are in {near['district']}, {near['city']} "
            f"({near['distance_km']:.1f} km from the district sensor). "
            f"Currently {near['temp_c']}°C, humidity {near['humidity']:.0%}, "
            f"wind {near['wind_kmh']} km/h with {near['rain_6h_mm']}mm rain in the "
            f"last 6 hours. Flood risk is {flood_p:.0%}, fire risk {fire_p:.0%}, "
            f"accident probability {accident_p:.0%}. "
            + (tips[0] if tips else "")
        )
    else:
        weather_brief = {k: near[k] for k in
                         ("temp_c", "humidity", "wind_kmh", "rain_6h_mm", "river_level_m")}
        summary = await gemini.generate(
            f"You are Sentinel AI. Write a 3-sentence situational briefing for a "
            f"citizen currently in {near['district']}, {near['city']}. "
            f"Live weather: {weather_brief}. Model risks: flood {flood_p:.0%}, "
            f"fire {fire_p:.0%}, accident {accident_p:.0%}. Nearest hospitals with "
            f"occupancy: {[(h['hospital'], h['occupancy']) for h in hospitals]}. "
            f"Be specific, calm and practical — no preamble.")

    return {
        "district": near["district"],
        "city": near["city"],
        "distance_km": round(float(near["distance_km"]), 1),
        "weather": {
            "temp_c": float(near["temp_c"]), "humidity": float(near["humidity"]),
            "wind_kmh": float(near["wind_kmh"]), "rain_6h_mm": float(near["rain_6h_mm"]),
            "river_level_m": float(near["river_level_m"]),
        },
        "risks": {
            "flood": round(flood_p, 3), "fire": round(fire_p, 3),
            "accident": round(accident_p, 3),
            "flood_explanation": explain_prediction(flood_model, flood_X, flood_p)["narrative"],
        },
        "nearest_hospitals": hospitals,
        "ai_summary": summary,
        "suggestions": tips,
    }
