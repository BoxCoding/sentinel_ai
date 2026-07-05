"""Traffic Agent: congestion + closures from sensors and Google Maps;
computes best emergency routes avoiding hazards."""
from app.agents.base import AgentResult, BaseAgent
from app.ml.predictors import engine
from app.services.bigquery_svc import bq
from app.services.maps_svc import maps


class TrafficAgent(BaseAgent):
    name = "traffic"

    async def run(self, context: dict) -> AgentResult:
        sensors = bq.table("traffic_sensors")
        closures = bq.table("road_closures")
        hotspots = []
        if not sensors.empty:
            for _, row in sensors.iterrows():
                if row["congestion_index"] > 0.75:
                    hotspots.append({
                        "road": row["road"], "district": row["district"],
                        "congestion_index": row["congestion_index"],
                        "avg_speed_kmh": row["avg_speed_kmh"],
                    })
        closed = closures.to_dict("records") if not closures.empty else []

        # emergency route request in context (e.g., ambulance dispatch)
        route = None
        if origin := context.get("route_origin"):
            route = await maps.best_route(tuple(origin),
                                          tuple(context["route_destination"]),
                                          avoid_flooded=True)

        forecast = engine.traffic_congestion_forecast(
            context.get("district", "Central"), horizon_hours=6)
        risk = max((h["congestion_index"] for h in hotspots), default=0.3)
        recs = [f"Reroute emergency traffic off {h['road']} "
                f"(congestion {h['congestion_index']:.0%})" for h in hotspots[:3]]
        recs += [f"Road closed: {c['road']} — {c['reason']}" for c in closed[:3]]
        return AgentResult(
            agent=self.name, risk_score=float(risk), confidence=0.84,
            summary=f"{len(hotspots)} congestion hotspots, {len(closed)} road closures.",
            data={"hotspots": hotspots, "closures": closed,
                  "congestion_forecast": forecast, "emergency_route": route},
            recommendations=recs or ["Traffic network normal; no rerouting needed."],
        )
