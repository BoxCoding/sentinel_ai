"""Conversational AI endpoint. Routes queries: SOP/guideline questions to the
RAG agent, "what should we do" to a decision cycle, otherwise Gemini with a
situational-context system prompt (mirrors the ADK coordinator's routing)."""
from fastapi import APIRouter, Depends

from app.agents.orchestrator import orchestrator
from app.agents.rag_agent import RAGAgent
from app.core.security import get_current_user
from app.schemas.api import ChatRequest
from app.services.firestore_db import fs
from app.services.gemini import gemini

router = APIRouter(prefix="/chat", tags=["chat"])

RAG_HINTS = ("sop", "procedure", "protocol", "guideline", "manual", "policy",
             "rule", "should we", "how do we", "what is the")
DECISION_HINTS = ("what should", "recommend", "deploy", "action plan",
                  "priorit", "decide", "allocate")


@router.post("")
async def chat(body: ChatRequest, user=Depends(get_current_user)):
    text = body.message.lower()
    mode = body.mode
    if mode == "auto":
        if any(h in text for h in DECISION_HINTS):
            mode = "decision"
        elif any(h in text for h in RAG_HINTS):
            mode = "rag"
        else:
            mode = "general"

    if mode == "rag":
        result = await RAGAgent().execute({"question": body.message})
        response = {"mode": "rag", "answer": result.data.get("answer", result.summary),
                    "citations": result.data.get("citations", [])}
    elif mode == "decision":
        cycle = await orchestrator.run_decision_cycle({"question": body.message})
        decision = cycle["decision"]["data"]
        response = {"mode": "decision", "answer": decision.get("reasoning", ""),
                    "risk_score": decision.get("risk_score"),
                    "priority": decision.get("priority"),
                    "action_plan": decision.get("action_plan", [])}
    else:
        answer = await gemini.generate(
            body.message,
            system=("You are Sentinel AI, the city's emergency decision assistant. "
                    "Be concise, quantitative, and action-oriented."),
        )
        response = {"mode": "general", "answer": answer}

    fs.add("chat_history", {"user": user.username, "message": body.message,
                            "mode": response["mode"],
                            "answer": response["answer"][:2000]})
    return response
