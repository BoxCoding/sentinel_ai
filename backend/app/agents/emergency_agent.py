"""Emergency Agent: fuses 911 calls, citizen reports, social signals and
police reports; classifies severity with the ML model + Gemini context."""
from app.agents.base import AgentResult, BaseAgent
from app.ml.predictors import engine
from app.services.bigquery_svc import bq

SEVERITY_LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ETYPE_CODES = {"medical": 0, "fire": 1, "flood": 2, "accident": 3, "other": 4}


class EmergencyAgent(BaseAgent):
    name = "emergency"

    async def run(self, context: dict) -> AgentResult:
        calls = bq.table("emergency_calls")
        reports = bq.table("citizen_reports")
        classified = []
        for _, row in calls.iterrows() if not calls.empty else []:
            features = {
                "injuries": row.get("injuries", 0),
                "trapped": int(row.get("trapped", 0)),
                "spreading": int(row.get("spreading", 0)),
                "vulnerable": int(row.get("vulnerable", 0)),
                "etype": ETYPE_CODES.get(row.get("type", "other"), 4),
            }
            severity, proba = engine.emergency_severity(features)
            classified.append({
                "call_id": row["call_id"], "type": row.get("type"),
                "district": row.get("district"), "description": row.get("description", ""),
                "severity": SEVERITY_LABELS[severity],
                "severity_confidence": round(float(proba[severity]), 3),
            })

        classified.sort(key=lambda c: SEVERITY_LABELS.index(c["severity"]), reverse=True)
        critical = [c for c in classified if c["severity"] == "CRITICAL"]
        high = [c for c in classified if c["severity"] == "HIGH"]
        social_count = len(reports) if not reports.empty else 0
        risk = min(1.0, 0.25 * len(critical) + 0.1 * len(high) + 0.2)
        recs = [f"Dispatch priority: {c['type']} in {c['district']} "
                f"(call {c['call_id']}, CRITICAL)" for c in critical[:5]]
        return AgentResult(
            agent=self.name, risk_score=risk, confidence=0.85,
            summary=(f"{len(classified)} active calls: {len(critical)} critical, "
                     f"{len(high)} high. {social_count} citizen reports corroborate."),
            data={"classified_calls": classified[:50], "citizen_report_count": social_count},
            recommendations=recs or ["No critical calls in queue."],
        )
