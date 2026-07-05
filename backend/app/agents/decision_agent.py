"""Decision Agent: fuses every agent's output into a ranked, explainable
action plan — risk score, confidence, reasoning, priority, estimated impact."""
from app.agents.base import AgentResult, BaseAgent
from app.services.firestore_db import fs
from app.services.gemini import gemini

FUSION_WEIGHTS = {"weather": 0.25, "hospital": 0.20, "emergency": 0.25,
                  "traffic": 0.10, "prediction": 0.20}


class DecisionAgent(BaseAgent):
    name = "decision"

    async def run(self, context: dict) -> AgentResult:
        agent_results: dict[str, AgentResult] = context.get("agent_results", {})
        weighted, total_weight = 0.0, 0.0
        for name, weight in FUSION_WEIGHTS.items():
            result = agent_results.get(name)
            if result and result.risk_score is not None and result.status == "ok":
                weighted += weight * result.risk_score * result.confidence
                total_weight += weight * result.confidence
        composite = weighted / total_weight if total_weight else 0.3

        priority = ("P1-CRITICAL" if composite > 0.75 else
                    "P2-HIGH" if composite > 0.55 else
                    "P3-ELEVATED" if composite > 0.35 else "P4-ROUTINE")

        briefing = "\n".join(
            f"- {name.upper()}: risk={r.risk_score}, confidence={r.confidence:.2f} — {r.summary}"
            for name, r in agent_results.items() if r.status == "ok"
        )
        reasoning = await gemini.generate(
            "You are the city Emergency Operations Center decision AI. Given these "
            f"agent reports:\n{briefing}\n\nComposite risk: {composite:.0%} "
            f"({priority}). Produce a concise action plan: top 5 actions in priority "
            "order with responsible unit and expected impact.",
        )
        actions = []
        for name, r in agent_results.items():
            for rec in r.recommendations[:2]:
                actions.append({"source_agent": name, "action": rec})

        decision = {
            "risk_score": round(composite, 3),
            "confidence": round(min((r.confidence for r in agent_results.values()
                                     if r.status == "ok"), default=0.5), 3),
            "priority": priority,
            "reasoning": reasoning,
            "action_plan": actions,
            "estimated_impact": self._impact(composite),
            "supporting_data": {n: r.summary for n, r in agent_results.items()},
        }
        decision_id = fs.add("decisions", decision)
        return AgentResult(
            agent=self.name, risk_score=composite, confidence=decision["confidence"],
            summary=f"{priority}: composite risk {composite:.0%}. {len(actions)} actions planned.",
            data={"decision_id": decision_id, **decision},
            recommendations=[a["action"] for a in actions[:5]],
        )

    def _impact(self, risk: float) -> str:
        if risk > 0.75:
            return "City-scale: 10,000+ residents potentially affected; multi-agency response."
        if risk > 0.55:
            return "District-scale: 1,000-10,000 residents; coordinated two-agency response."
        if risk > 0.35:
            return "Local: under 1,000 residents; single-agency response sufficient."
        return "Minimal: routine operations."
