"""Vision Agent: two-stage image triage — Vision AI labels for fast hazard
flags, then Gemini 2.5 Pro multimodal for scene understanding and severity."""
from app.agents.base import AgentResult, BaseAgent
from app.services.gemini import gemini
from app.services.storage_svc import storage
from app.services.vision_svc import vision

ANALYSIS_PROMPT = (
    "You are an emergency-response image analyst. Identify hazards (fire, flood, "
    "smoke, accident, road blockage, collapsed building, damaged infrastructure), "
    "estimate severity (LOW/MEDIUM/HIGH/CRITICAL), note visible casualties or "
    "trapped persons, and state whether the road/area is passable for emergency "
    "vehicles. Be specific and factual."
)


class VisionAgent(BaseAgent):
    name = "vision"

    async def run(self, context: dict) -> AgentResult:
        image_bytes: bytes | None = context.get("image_bytes")
        mime = context.get("mime_type", "image/jpeg")
        if image_bytes is None:
            return AgentResult(agent=self.name, status="degraded",
                               summary="No image provided.")

        gcs_uri = storage.upload(image_bytes, f"uploads/{context.get('filename', 'frame.jpg')}",
                                 content_type=mime)
        triage = vision.detect_hazards(image_bytes)
        analysis = await gemini.analyze_media(image_bytes, mime, ANALYSIS_PROMPT)

        hazards = triage["hazards"]
        severity_score = {"FIRE": 0.85, "COLLAPSE": 0.9, "FLOOD": 0.75,
                          "ACCIDENT": 0.7, "SMOKE": 0.6, "ROAD_BLOCKAGE": 0.5}
        risk = max((severity_score.get(h, 0.4) for h in hazards), default=0.2)
        return AgentResult(
            agent=self.name, risk_score=risk,
            confidence=max((l["score"] for l in triage["labels"]), default=0.5),
            summary=f"Hazards detected: {', '.join(hazards) or 'none'}.",
            data={"gcs_uri": gcs_uri, "vision_labels": triage["labels"],
                  "hazards": hazards, "gemini_analysis": analysis},
            recommendations=(
                [f"Confirmed {h.lower().replace('_', ' ')} — dispatch appropriate unit."
                 for h in hazards] or ["No hazards visible; archive frame."]
            ),
        )
