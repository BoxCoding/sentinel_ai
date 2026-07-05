"""Incident CRUD + multimodal reporting (voice call, image evidence)."""
from fastapi import APIRouter, Depends, File, UploadFile

from app.agents.vision_agent import VisionAgent
from app.agents.voice_agent import VoiceAgent
from app.core.config import settings
from app.core.security import get_current_user, require_role
from app.schemas.api import IncidentCreate
from app.services.firestore_db import fs
from app.services.pubsub_svc import pubsub

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("")
async def list_incidents(limit: int = 50, _=Depends(get_current_user)):
    return fs.list("incidents", limit=limit)


@router.post("")
async def create_incident(body: IncidentCreate, user=Depends(get_current_user)):
    incident = {**body.model_dump(), "source": "manual", "status": "open",
                "reporter": body.reporter or user.username}
    incident_id = fs.add("incidents", incident)
    pubsub.publish(settings.TOPIC_INCIDENTS, {"incident_id": incident_id, **incident})
    return {"incident_id": incident_id, **incident}


@router.post("/report/voice")
async def report_voice(file: UploadFile = File(...), _=Depends(get_current_user)):
    """Emergency call audio -> STT -> structured incident."""
    audio = await file.read()
    result = await VoiceAgent().execute({"audio_bytes": audio, "filename": file.filename})
    if incident_id := result.data.get("incident_id"):
        pubsub.publish(settings.TOPIC_INCIDENTS,
                       {"incident_id": incident_id, "source": "voice_call"})
    return result.model_dump()


@router.post("/report/image")
async def report_image(file: UploadFile = File(...), _=Depends(get_current_user)):
    """CCTV frame / citizen photo -> Vision AI + Gemini hazard analysis."""
    image = await file.read()
    result = await VisionAgent().execute({
        "image_bytes": image, "mime_type": file.content_type or "image/jpeg",
        "filename": file.filename,
    })
    return result.model_dump()


@router.patch("/{incident_id}/status")
async def update_status(incident_id: str, status: str,
                        _=Depends(require_role("responder"))):
    fs.update("incidents", incident_id, {"status": status})
    return {"incident_id": incident_id, "status": status}
