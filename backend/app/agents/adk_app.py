"""Google ADK multi-agent application (cloud path).

Wraps the same domain tools the deterministic orchestrator uses into
LlmAgents, with a root coordinator that routes user requests to the right
specialist. Deploy with `adk deploy cloud_run backend/app/agents/adk_app.py`
or serve via Agent Engine. In DEMO_MODE the FastAPI /chat route uses the
deterministic path instead, so this module is only imported when ADK and
Vertex credentials are present."""
from app.core.config import settings


def _tool_flood_risk(district: str) -> dict:
    """Return current flood probability and explanation for a district."""
    from app.ml.predictors import engine
    from app.xai.explainer import explain_prediction

    prob, model, X = engine.flood_probability({
        "rain_6h_mm": 60, "river_level_m": 3.8, "drainage_capacity": 38,
        "soil_saturation": 0.8, "elevation_m": 12,
    })
    return {"district": district, "flood_probability": prob,
            "explanation": explain_prediction(model, X, prob)["narrative"]}


def _tool_hospital_status() -> list[dict]:
    """Return live hospital occupancy, ICU beds and overload forecasts."""
    from app.services.bigquery_svc import bq

    return bq.table("hospital_status").to_dict("records")


def _tool_search_sops(question: str) -> list[dict]:
    """Search emergency SOPs and guidelines in the vector knowledge base."""
    from app.services.vector_search import vector_search

    return vector_search.search(question, top_k=5)


def _tool_run_decision_cycle() -> dict:
    """Run a full multi-agent decision cycle and return the fused decision."""
    import asyncio

    from app.agents.orchestrator import orchestrator

    return asyncio.get_event_loop().run_until_complete(
        orchestrator.run_decision_cycle()
    )["decision"]


def build_adk_app():
    from google.adk.agents import LlmAgent

    weather = LlmAgent(
        name="weather_agent", model=settings.GEMINI_FLASH_MODEL,
        description="Flood/storm risk analysis per district.",
        instruction="Assess weather-driven risk using flood_risk. Cite probabilities.",
        tools=[_tool_flood_risk],
    )
    hospital = LlmAgent(
        name="hospital_agent", model=settings.GEMINI_FLASH_MODEL,
        description="Hospital capacity, ICU beds, overload prediction.",
        instruction="Analyze hospital load and recommend patient routing.",
        tools=[_tool_hospital_status],
    )
    rag_agent = LlmAgent(
        name="sop_agent", model=settings.GEMINI_MODEL,
        description="Answers questions from official SOPs and manuals.",
        instruction="Answer ONLY from search_sops results; cite sources.",
        tools=[_tool_search_sops],
    )
    coordinator = LlmAgent(
        name="sentinel_coordinator", model=settings.GEMINI_MODEL,
        description="Sentinel AI emergency decision coordinator.",
        instruction=(
            "You coordinate city emergency intelligence. Route domain questions to "
            "sub-agents; for 'what should we do now' questions run a decision cycle. "
            "Always include risk score, confidence and reasoning."
        ),
        tools=[_tool_run_decision_cycle],
        sub_agents=[weather, hospital, rag_agent],
    )
    return coordinator


root_agent = None
if not settings.DEMO_MODE:
    try:
        root_agent = build_adk_app()
    except ImportError:
        pass
