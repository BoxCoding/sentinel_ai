"""Aggregated data for dashboard pages: home KPIs, map layers, timelines,
per-domain dashboards, admin views."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user, require_role
from app.services.bigquery_svc import bq
from app.services.firestore_db import fs

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(_=Depends(get_current_user)):
    from app.core.config import settings
    from app.services.gemini import gemini
    from app.services.live_weather import _cache as weather_cache

    incidents = fs.list("incidents", limit=200)
    decisions = fs.list("decision_cycles", limit=10)
    hospitals = bq.table("hospital_status")
    calls = bq.table("emergency_calls")
    return {
        "ai": {"connected": gemini.connected, "model": gemini.active_model},
        "weather_source": ("open-meteo-live"
                           if settings.LIVE_WEATHER and weather_cache["df"] is not None
                           else "synthetic"),
        "open_incidents": sum(1 for i in incidents if i.get("status") == "open"),
        "total_incidents_today": len(incidents),
        "active_calls": len(calls) if not calls.empty else 0,
        "avg_hospital_occupancy": (round(float(hospitals["occupancy"].mean()), 3)
                                   if not hospitals.empty else None),
        "latest_risk_score": (decisions[0].get("risk_score") if decisions else None),
        "latest_priority": (decisions[0].get("priority") if decisions else None),
        "recent_decisions": decisions[:5],
    }


@router.get("/map")
async def map_layers(_=Depends(get_current_user)):
    incidents = fs.list("incidents", limit=100)
    hospitals = bq.table("hospital_status")
    closures = bq.table("road_closures")
    weather = bq.table("weather_current")
    return {
        "incidents": [i for i in incidents if i.get("lat")],
        "hospitals": hospitals.to_dict("records") if not hospitals.empty else [],
        "road_closures": closures.to_dict("records") if not closures.empty else [],
        "flood_zones": (weather[["district", "city", "lat", "lng", "rain_6h_mm"]]
                        .to_dict("records") if not weather.empty else []),
    }


@router.get("/timeline")
async def timeline(limit: int = 50, _=Depends(get_current_user)):
    events = (fs.list("incidents", limit=limit)
              + fs.list("decision_cycles", limit=limit)
              + fs.list("notifications", limit=limit))
    events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    return events[:limit]


@router.get("/hospitals")
async def hospitals(_=Depends(get_current_user)):
    df = bq.table("hospital_status")
    return df.to_dict("records") if not df.empty else []


@router.get("/weather")
async def weather(_=Depends(get_current_user)):
    df = bq.table("weather_current")
    return df.to_dict("records") if not df.empty else []


@router.get("/traffic")
async def traffic(_=Depends(get_current_user)):
    sensors = bq.table("traffic_sensors")
    closures = bq.table("road_closures")
    return {"sensors": sensors.to_dict("records") if not sensors.empty else [],
            "closures": closures.to_dict("records") if not closures.empty else []}


@router.get("/admin/audit")
async def audit(limit: int = 100, _=Depends(require_role("admin"))):
    return {"notifications": fs.list("notifications", limit=limit),
            "work_orders": fs.list("work_orders", limit=limit),
            "incident_reports": fs.list("incident_reports", limit=limit),
            "agent_runs": fs.list("agent_runs", limit=limit)}
