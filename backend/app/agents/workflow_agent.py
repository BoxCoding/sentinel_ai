"""Workflow Agent: turns decisions into automated actions — notifications
to hospitals/police/ambulance/citizens, work orders, incident reports.
Every action is published to Pub/Sub and logged for audit."""
from app.agents.base import AgentResult, BaseAgent
from app.core.config import settings
from app.services.firestore_db import fs
from app.services.notifications import notifier
from app.services.pubsub_svc import pubsub


class WorkflowAgent(BaseAgent):
    name = "workflow"

    async def run(self, context: dict) -> AgentResult:
        decision: dict = context.get("decision", {})
        risk = decision.get("risk_score", 0.0)
        priority = decision.get("priority", "P4-ROUTINE")
        incident_id = context.get("incident_id")
        executed: list[str] = []

        if risk >= settings.CRITICAL_RISK_THRESHOLD or priority.startswith("P1"):
            for org, channel in [("disaster-team@city.gov", "email"),
                                 ("police-dispatch@city.gov", "email"),
                                 ("hospital-network@city.gov", "email"),
                                 ("ambulance-control@city.gov", "email")]:
                notifier.notify(channel, org, f"[{priority}] Sentinel AI Alert",
                                decision.get("reasoning", "")[:1000], incident_id)
                executed.append(f"Notified {org}")
            notifier.broadcast_citizens("affected-zones",
                                        "Emergency advisory: follow official instructions. "
                                        "Avoid low-lying roads.", incident_id)
            executed.append("Citizen broadcast issued")

            work_order = {
                "type": "emergency_response", "priority": priority,
                "actions": decision.get("action_plan", []), "status": "dispatched",
                "incident_id": incident_id,
            }
            wo_id = fs.add("work_orders", work_order)
            executed.append(f"Work order {wo_id} created")

            report = {
                "incident_id": incident_id, "risk_score": risk, "priority": priority,
                "reasoning": decision.get("reasoning", ""),
                "actions_taken": executed,
            }
            report_id = fs.add("incident_reports", report)
            executed.append(f"Incident report {report_id} generated")
        elif risk >= 0.5:
            notifier.notify("email", "eoc-duty-officer@city.gov",
                            f"[{priority}] Sentinel AI advisory",
                            decision.get("reasoning", "")[:1000], incident_id)
            executed.append("EOC duty officer advised")
        else:
            executed.append("Risk below action threshold; logged only.")

        pubsub.publish(settings.TOPIC_WORKFLOWS, {
            "incident_id": incident_id, "priority": priority,
            "risk_score": risk, "actions": executed,
        })
        return AgentResult(
            agent=self.name, confidence=0.95,
            summary=f"{len(executed)} workflow actions executed for {priority}.",
            data={"executed": executed},
            recommendations=executed,
        )
