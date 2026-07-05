"""Orchestrator: runs the situational agents in parallel, then the Decision
Agent fuses their outputs, then the Workflow Agent executes automations.

This is the deterministic decision loop triggered by Cloud Scheduler (every
5 minutes in production) and on-demand from the dashboard. Conversational
multi-agent routing lives in adk_app.py (Google ADK)."""
import asyncio

from app.agents.base import AgentResult
from app.agents.decision_agent import DecisionAgent
from app.agents.emergency_agent import EmergencyAgent
from app.agents.hospital_agent import HospitalAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.traffic_agent import TrafficAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.workflow_agent import WorkflowAgent
from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import record_metric
from app.services.firestore_db import fs
from app.services.pubsub_svc import pubsub

log = get_logger(__name__)

SITUATIONAL_AGENTS = [WeatherAgent, TrafficAgent, HospitalAgent,
                      EmergencyAgent, PredictionAgent]


class Orchestrator:
    async def run_decision_cycle(self, context: dict | None = None) -> dict:
        context = context or {}
        agents = [cls() for cls in SITUATIONAL_AGENTS]
        results: list[AgentResult] = await asyncio.gather(
            *(agent.execute(context) for agent in agents)
        )
        agent_results = {r.agent: r for r in results}

        decision_result = await DecisionAgent().execute(
            {**context, "agent_results": agent_results}
        )
        workflow_result = await WorkflowAgent().execute(
            {**context, "decision": decision_result.data,
             "incident_id": context.get("incident_id")}
        )

        cycle = {
            "agents": {name: r.model_dump() for name, r in agent_results.items()},
            "decision": decision_result.model_dump(),
            "workflow": workflow_result.model_dump(),
        }
        cycle_id = fs.add("decision_cycles", {
            "risk_score": decision_result.risk_score,
            "priority": decision_result.data.get("priority"),
            "summary": decision_result.summary,
        })
        cycle["cycle_id"] = cycle_id
        pubsub.publish(settings.TOPIC_ALERTS, {
            "cycle_id": cycle_id, "risk_score": decision_result.risk_score,
            "priority": decision_result.data.get("priority"),
        })
        record_metric("risk_score", decision_result.risk_score or 0.0,
                      {"priority": decision_result.data.get("priority", "unknown")})
        log.info("decision_cycle_complete", cycle_id=cycle_id,
                 risk=decision_result.risk_score)
        return cycle


orchestrator = Orchestrator()
