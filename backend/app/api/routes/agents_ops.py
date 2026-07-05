"""Agent operations: trigger decision cycles, inspect agent runs, RAG ingest,
emergency routing."""
from fastapi import APIRouter, Depends, File, UploadFile

from app.agents.orchestrator import orchestrator
from app.core.security import get_current_user, require_role
from app.rag.pipeline import rag
from app.schemas.api import RouteRequest
from app.services.firestore_db import fs
from app.services.maps_svc import maps

router = APIRouter(tags=["agents"])


@router.post("/agents/decision-cycle")
async def run_decision_cycle(_=Depends(require_role("responder"))):
    """Run the full multi-agent decision loop (also fired by Cloud Scheduler)."""
    return await orchestrator.run_decision_cycle()


@router.get("/agents/runs")
async def agent_runs(limit: int = 30, _=Depends(get_current_user)):
    return fs.list("agent_runs", limit=limit)


@router.get("/decisions")
async def decisions(limit: int = 20, _=Depends(get_current_user)):
    return fs.list("decisions", limit=limit)


@router.post("/rag/ingest")
async def rag_ingest(file: UploadFile = File(...), source_type: str = "sop",
                     _=Depends(require_role("commander"))):
    content = await file.read()
    return rag.ingest_document(file.filename, content,
                               file.content_type or "application/pdf", source_type)


@router.post("/routes/emergency")
async def emergency_route(body: RouteRequest, _=Depends(get_current_user)):
    return await maps.best_route((body.origin_lat, body.origin_lng),
                                 (body.dest_lat, body.dest_lng),
                                 avoid_flooded=body.avoid_flooded)
