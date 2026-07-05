"""RAG Agent: grounded Q&A over SOPs, guidelines and manuals via
Document AI -> Embeddings -> Vertex AI Vector Search -> Gemini."""
from app.agents.base import AgentResult, BaseAgent
from app.rag.pipeline import rag


class RAGAgent(BaseAgent):
    name = "rag"

    async def run(self, context: dict) -> AgentResult:
        question = context.get("question", "")
        if not question:
            return AgentResult(agent=self.name, status="degraded",
                               summary="No question provided.")
        result = await rag.answer(question)
        return AgentResult(
            agent=self.name,
            confidence=max((c["score"] for c in result["citations"]), default=0.5),
            summary=result["answer"][:300],
            data=result,
            recommendations=[f"Grounded in {len(result['citations'])} SOP excerpts."],
        )
