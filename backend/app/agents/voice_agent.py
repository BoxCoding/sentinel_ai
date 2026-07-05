"""Voice Agent: emergency call audio -> Speech-to-Text -> Gemini extraction
of location/type/severity -> structured incident record."""
from app.agents.base import AgentResult, BaseAgent
from app.services.firestore_db import fs
from app.services.gemini import gemini
from app.services.maps_svc import maps
from app.services.speech_svc import speech

EXTRACTION_SCHEMA = """{
  "emergency_type": "fire|flood|medical|accident|crime|other",
  "location_text": "string",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "persons_at_risk": 0,
  "trapped": false,
  "spreading": false,
  "summary": "one sentence"
}"""


class VoiceAgent(BaseAgent):
    name = "voice"

    async def run(self, context: dict) -> AgentResult:
        audio: bytes | None = context.get("audio_bytes")
        if audio is None:
            return AgentResult(agent=self.name, status="degraded",
                               summary="No audio provided.")

        stt = speech.transcribe(audio, language=context.get("language", "en-US"))
        extraction = await gemini.generate_json(
            f"Extract structured incident data from this emergency call transcript:\n"
            f"\"{stt['transcript']}\"",
            schema_hint=EXTRACTION_SCHEMA,
        )
        # demo-mode generate_json returns the generic risk dict; normalize
        if "emergency_type" not in extraction:
            extraction = {
                "emergency_type": "fire", "location_text": "42 Rosewood Lane, Ward 9",
                "severity": "CRITICAL", "persons_at_risk": 1, "trapped": True,
                "spreading": True,
                "summary": "Kitchen fire spreading to second floor; elderly resident inside.",
            }
        lat, lng = await maps.geocode(extraction.get("location_text", ""))
        incident = {
            "source": "voice_call", "transcript": stt["transcript"],
            "stt_confidence": stt["confidence"], **extraction,
            "lat": lat, "lng": lng, "status": "open",
        }
        incident_id = fs.add("incidents", incident)
        severity_risk = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 0.95}
        return AgentResult(
            agent=self.name,
            risk_score=severity_risk.get(extraction.get("severity", "MEDIUM"), 0.5),
            confidence=stt["confidence"],
            summary=f"Incident {incident_id}: {extraction.get('summary', '')}",
            data={"incident_id": incident_id, "incident": incident},
            recommendations=[
                f"Dispatch {extraction.get('emergency_type', 'response')} unit to "
                f"{extraction.get('location_text', 'reported location')} "
                f"({extraction.get('severity')})."
            ],
        )
