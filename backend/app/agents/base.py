"""Agent framework base.

Each Sentinel agent implements `run(context) -> AgentResult`. The same tool
functions are exported to Google ADK LlmAgents in adk_app.py for the
cloud-deployed conversational agent mesh; this class hierarchy is the
deterministic orchestration path used by the Decision pipeline, where
reproducibility and latency matter more than free-form LLM planning."""
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.firestore_db import fs


class AgentResult(BaseModel):
    agent: str
    status: str = "ok"                      # ok | degraded | error
    risk_score: float | None = None         # 0..1 where applicable
    confidence: float = 0.8
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    duration_ms: int = 0


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self):
        self.log = get_logger(f"agent.{self.name}")

    @abstractmethod
    async def run(self, context: dict) -> AgentResult:
        ...

    async def execute(self, context: dict) -> AgentResult:
        """Run with timing, audit logging, and error containment."""
        start = time.monotonic()
        try:
            result = await self.run(context)
        except Exception as exc:
            self.log.error("agent_failed", error=str(exc))
            result = AgentResult(agent=self.name, status="error", confidence=0.0,
                                 summary=f"Agent failed: {exc}")
        result.duration_ms = int((time.monotonic() - start) * 1000)
        fs.add("agent_runs", result.model_dump())
        return result
