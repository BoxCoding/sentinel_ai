"""Hospital Agent: occupancy/ICU/staffing analysis, overload forecasting,
patient routing recommendations per the surge protocol."""
from app.agents.base import AgentResult, BaseAgent
from app.ml.predictors import engine
from app.services.bigquery_svc import bq

OVERFLOW_PAIRS = {
    "AIIMS Delhi": "Fortis Noida", "Fortis Noida": "AIIMS Delhi",
    "Medanta Gurugram": "AIIMS Delhi",
    "Lilavati Mumbai": "KEM Mumbai", "KEM Mumbai": "Lilavati Mumbai",
    "Manipal Bengaluru": "St. John's Bengaluru",
    "St. John's Bengaluru": "Manipal Bengaluru",
}


class HospitalAgent(BaseAgent):
    name = "hospital"

    async def run(self, context: dict) -> AgentResult:
        hospitals = bq.table("hospital_status")
        if hospitals.empty:
            return AgentResult(agent=self.name, status="degraded",
                               summary="No hospital telemetry available.")

        statuses, recs, overload_risks = [], [], []
        for _, row in hospitals.iterrows():
            forecast = engine.hospital_occupancy_forecast(row["hospital"], horizon_days=3)
            will_overload = any(f["overload_risk"] for f in forecast)
            statuses.append({
                "hospital": row["hospital"], "occupancy": row["occupancy"],
                "icu_beds_free": row["icu_beds_free"], "doctors_on_duty": row["doctors_on_duty"],
                "medicine_stock_days": row["medicine_stock_days"],
                "forecast": forecast, "overload_predicted": will_overload,
            })
            overload_risks.append(max(row["occupancy"],
                                      max((f["predicted_occupancy"] for f in forecast), default=0)))
            if row["occupancy"] > 0.90:
                recs.append(f"{row['hospital']} at {row['occupancy']:.0%} — activate surge mode; "
                            f"divert non-critical to {OVERFLOW_PAIRS.get(row['hospital'], 'nearest <80%')}.")
            elif will_overload:
                recs.append(f"{row['hospital']} forecast to exceed 90% within 3 days — "
                            "expedite discharge-ready patients now.")
            if row["medicine_stock_days"] < 3:
                recs.append(f"{row['hospital']} medicine stock below 3 days — trigger resupply order.")

        return AgentResult(
            agent=self.name, risk_score=float(max(overload_risks)), confidence=0.87,
            summary=(f"{sum(s['occupancy'] > 0.9 for s in statuses)} hospitals in surge, "
                     f"{sum(s['overload_predicted'] for s in statuses)} forecast to overload."),
            data={"hospitals": statuses},
            recommendations=recs or ["All hospitals within capacity."],
        )
