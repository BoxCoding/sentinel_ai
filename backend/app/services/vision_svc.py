"""Vision AI label/object detection — first-pass triage of CCTV, drone and
citizen images before Gemini does the deep multimodal analysis."""
from app.core.config import settings

HAZARD_LABELS = {
    "fire": "FIRE", "flame": "FIRE", "smoke": "SMOKE",
    "flood": "FLOOD", "water": "FLOOD",
    "car crash": "ACCIDENT", "vehicle": "ACCIDENT", "wreck": "ACCIDENT",
    "rubble": "COLLAPSE", "debris": "ROAD_BLOCKAGE",
}


class VisionService:
    def detect_hazards(self, image_bytes: bytes) -> dict:
        if settings.DEMO_MODE:
            return {
                "labels": [{"label": "Flood", "score": 0.91}, {"label": "Vehicle", "score": 0.84}],
                "hazards": ["FLOOD", "ACCIDENT"],
            }
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()
        response = client.label_detection(image=vision.Image(content=image_bytes))
        labels = [{"label": l.description, "score": l.score} for l in response.label_annotations]
        hazards = sorted({
            hazard for l in labels
            for key, hazard in HAZARD_LABELS.items()
            if key in l["label"].lower() and l["score"] > 0.6
        })
        return {"labels": labels, "hazards": hazards}


vision = VisionService()
