"""Weather Agent: ingests station telemetry, flags heavy rainfall/storms,
runs the flood model per district, recommends warning levels."""
from app.agents.base import AgentResult, BaseAgent
from app.ml.predictors import engine
from app.services.bigquery_svc import bq
from app.xai.explainer import explain_prediction


class WeatherAgent(BaseAgent):
    name = "weather"

    async def run(self, context: dict) -> AgentResult:
        weather = bq.table("weather_current")
        if weather.empty:
            return AgentResult(agent=self.name, status="degraded",
                               summary="No weather telemetry available.")

        district_risks, warnings = [], []
        for _, row in weather.iterrows():
            features = {
                "rain_6h_mm": row["rain_6h_mm"], "river_level_m": row["river_level_m"],
                "drainage_capacity": row["drainage_capacity"],
                "soil_saturation": row["soil_saturation"], "elevation_m": row["elevation_m"],
            }
            prob, model, X = engine.flood_probability(features)
            explanation = explain_prediction(model, X, prob)
            district_risks.append({
                "district": row["district"], "flood_probability": round(prob, 3),
                "rain_6h_mm": row["rain_6h_mm"], "wind_kmh": row.get("wind_kmh", 0),
                "explanation": explanation["narrative"],
            })
            if prob > 0.8:
                warnings.append(f"Level-3 flood warning for {row['district']} "
                                f"(probability {prob:.0%})")
            elif prob > 0.6:
                warnings.append(f"Level-2 flood alert for {row['district']} "
                                f"(probability {prob:.0%})")
            if row.get("wind_kmh", 0) > 70:
                warnings.append(f"Storm warning for {row['district']}: "
                                f"wind {row['wind_kmh']} km/h")

        district_risks.sort(key=lambda d: d["flood_probability"], reverse=True)
        worst = district_risks[0]
        return AgentResult(
            agent=self.name,
            risk_score=worst["flood_probability"],
            confidence=0.88,
            summary=(f"Highest flood risk: {worst['district']} "
                     f"({worst['flood_probability']:.0%}). {len(warnings)} active warnings."),
            data={"district_risks": district_risks, "warnings": warnings},
            recommendations=warnings or ["No weather warnings required."],
        )
