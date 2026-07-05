"""Pydantic request/response schemas for the public API."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class IncidentCreate(BaseModel):
    type: str = Field(pattern="^(fire|flood|medical|accident|crime|other)$")
    description: str
    district: str
    lat: float | None = None
    lng: float | None = None
    reporter: str | None = None


class ChatRequest(BaseModel):
    message: str
    mode: str = "auto"  # auto | rag | decision | general


class FloodPredictionRequest(BaseModel):
    rain_6h_mm: float = 60
    river_level_m: float = 3.5
    drainage_capacity: float = 40
    soil_saturation: float = 0.7
    elevation_m: float = 25


class AccidentPredictionRequest(BaseModel):
    congestion: float = 0.6
    rain_mm: float = 5
    hour: int = 18
    is_night: int = 0
    road_quality: float = 0.7


class FirePredictionRequest(BaseModel):
    temp_c: float = 30
    humidity: float = 0.4
    wind_kmh: float = 20
    building_age: float = 40
    industrial: int = 0


class RouteRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    avoid_flooded: bool = True
