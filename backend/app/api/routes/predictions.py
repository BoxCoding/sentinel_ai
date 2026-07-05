"""Prediction endpoints — every response includes an explainability block."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.ml.predictors import engine
from app.ml.synthetic import DISTRICTS, HOSPITALS
from app.schemas.api import (AccidentPredictionRequest, FirePredictionRequest,
                             FloodPredictionRequest)
from app.xai.explainer import explain_prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/flood")
async def predict_flood(body: FloodPredictionRequest, _=Depends(get_current_user)):
    prob, model, X = engine.flood_probability(body.model_dump())
    return {"flood_probability": round(prob, 3),
            "explanation": explain_prediction(model, X, prob)}


@router.post("/accident")
async def predict_accident(body: AccidentPredictionRequest, _=Depends(get_current_user)):
    prob, model, X = engine.accident_probability(body.model_dump())
    return {"accident_probability": round(prob, 3),
            "explanation": explain_prediction(model, X, prob)}


@router.post("/fire")
async def predict_fire(body: FirePredictionRequest, _=Depends(get_current_user)):
    prob, model, X = engine.fire_risk(body.model_dump())
    return {"fire_risk": round(prob, 3),
            "explanation": explain_prediction(model, X, prob)}


@router.get("/hospital-occupancy")
async def hospital_occupancy(hospital: str | None = None, days: int = 7,
                             _=Depends(get_current_user)):
    hospitals = [hospital] if hospital else HOSPITALS
    return {h: engine.hospital_occupancy_forecast(h, days) for h in hospitals}


@router.get("/ambulance-demand")
async def ambulance_demand(district: str | None = None, hours: int = 12,
                           _=Depends(get_current_user)):
    districts = [district] if district else DISTRICTS
    return {d: engine.ambulance_demand_forecast(d, hours) for d in districts}


@router.get("/traffic-congestion")
async def traffic_congestion(district: str | None = None, hours: int = 6,
                             _=Depends(get_current_user)):
    districts = [district] if district else DISTRICTS
    return {d: engine.traffic_congestion_forecast(d, hours) for d in districts}
