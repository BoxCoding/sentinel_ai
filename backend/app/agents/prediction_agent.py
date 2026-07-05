"""Prediction Agent: batch runs every ML model across districts/hospitals
to produce the citywide risk surface consumed by the Decision Agent."""
from app.agents.base import AgentResult, BaseAgent
from app.ml.predictors import engine
from app.ml.synthetic import DISTRICTS, HOSPITALS
from app.services.bigquery_svc import bq
from app.xai.explainer import explain_prediction


class PredictionAgent(BaseAgent):
    name = "prediction"

    async def run(self, context: dict) -> AgentResult:
        weather = bq.table("weather_current")
        weather_by_district = (
            {row["district"]: row for _, row in weather.iterrows()}
            if not weather.empty else {}
        )
        predictions = {"districts": [], "hospitals": []}
        for district in DISTRICTS:
            w = weather_by_district.get(district)
            flood_features = {
                "rain_6h_mm": w["rain_6h_mm"] if w is not None else 20,
                "river_level_m": w["river_level_m"] if w is not None else 3.0,
                "drainage_capacity": w["drainage_capacity"] if w is not None else 40,
                "soil_saturation": w["soil_saturation"] if w is not None else 0.5,
                "elevation_m": w["elevation_m"] if w is not None else 50,
            }
            flood_p, flood_model, flood_X = engine.flood_probability(flood_features)
            accident_p, _, _ = engine.accident_probability({
                "congestion": 0.6, "rain_mm": flood_features["rain_6h_mm"] / 6,
                "hour": 18, "is_night": 0, "road_quality": 0.7,
            })
            fire_p, _, _ = engine.fire_risk({
                "temp_c": w["temp_c"] if w is not None else 28,
                "humidity": w["humidity"] if w is not None else 0.6,
                "wind_kmh": w["wind_kmh"] if w is not None else 12,
                "building_age": 35, "industrial": int(district == "Industrial Zone"),
            })
            predictions["districts"].append({
                "district": district,
                "flood_probability": round(flood_p, 3),
                "accident_probability": round(accident_p, 3),
                "fire_risk": round(fire_p, 3),
                "ambulance_demand": engine.ambulance_demand_forecast(district, 6),
                "congestion_forecast": engine.traffic_congestion_forecast(district, 6),
                "flood_explanation": explain_prediction(flood_model, flood_X, flood_p),
            })
        for hospital in HOSPITALS:
            predictions["hospitals"].append({
                "hospital": hospital,
                "occupancy_forecast": engine.hospital_occupancy_forecast(hospital, 7),
            })

        worst = max(predictions["districts"],
                    key=lambda d: max(d["flood_probability"], d["fire_risk"],
                                      d["accident_probability"]))
        top_risk = max(worst["flood_probability"], worst["fire_risk"],
                       worst["accident_probability"])
        return AgentResult(
            agent=self.name, risk_score=float(top_risk), confidence=0.86,
            summary=f"Citywide risk surface computed; highest combined risk in {worst['district']}.",
            data=predictions,
            recommendations=[
                f"Focus monitoring on {worst['district']} "
                f"(flood {worst['flood_probability']:.0%}, fire {worst['fire_risk']:.0%}, "
                f"accident {worst['accident_probability']:.0%})."
            ],
        )
