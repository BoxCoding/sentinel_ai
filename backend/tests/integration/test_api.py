"""End-to-end API flow against the demo-mode app: login -> incident ->
predictions -> decision cycle -> workflow audit -> RAG chat."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    resp = client.post("/api/v1/auth/login",
                       json={"username": "commander", "password": "command123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_health(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_requires_auth(client):
    assert client.get("/api/v1/incidents").status_code == 401


def test_incident_lifecycle(client, auth):
    created = client.post("/api/v1/incidents", headers=auth, json={
        "type": "flood", "description": "Street flooding", "district": "Riverside",
        "lat": 12.945, "lng": 77.575,
    })
    assert created.status_code == 200
    incident_id = created.json()["incident_id"]
    listed = client.get("/api/v1/incidents", headers=auth).json()
    assert any(i["id"] == incident_id for i in listed)
    updated = client.patch(f"/api/v1/incidents/{incident_id}/status",
                           headers=auth, params={"status": "resolved"})
    assert updated.json()["status"] == "resolved"


def test_flood_prediction_with_explanation(client, auth):
    resp = client.post("/api/v1/predictions/flood", headers=auth, json={
        "rain_6h_mm": 95, "river_level_m": 4.2, "drainage_capacity": 35,
        "soil_saturation": 0.9, "elevation_m": 8,
    })
    body = resp.json()
    assert body["flood_probability"] > 0.7
    assert "narrative" in body["explanation"]


def test_decision_cycle_and_audit(client, auth):
    cycle = client.post("/api/v1/agents/decision-cycle", headers=auth).json()
    assert set(cycle["agents"]) == {"weather", "traffic", "hospital",
                                    "emergency", "prediction"}
    assert cycle["decision"]["data"]["priority"].startswith("P")
    # workflow actions must be auditable (admin only)
    admin_tok = client.post("/api/v1/auth/login",
                            json={"username": "admin", "password": "admin123"}).json()
    audit = client.get("/api/v1/dashboard/admin/audit",
                       headers={"Authorization": f"Bearer {admin_tok['access_token']}"}).json()
    assert audit["agent_runs"]
    # commander may NOT access admin audit
    assert client.get("/api/v1/dashboard/admin/audit", headers=auth).status_code == 403


def test_rag_chat_cites_sources(client, auth):
    resp = client.post("/api/v1/chat", headers=auth,
                       json={"message": "What is the hospital surge protocol?"}).json()
    assert resp["mode"] == "rag"
    assert len(resp["citations"]) > 0


def test_voice_report_creates_incident(client, auth):
    resp = client.post("/api/v1/incidents/report/voice", headers=auth,
                       files={"file": ("call.wav", b"demo-audio-bytes", "audio/wav")})
    body = resp.json()
    assert body["agent"] == "voice"
    assert body["data"]["incident"]["emergency_type"] == "fire"


def test_location_briefing_gurugram(client, auth):
    """Coordinates in Gurugram must resolve to the Gurugram district with
    weather, risks, nearest hospitals and AI suggestions."""
    resp = client.post("/api/v1/location/briefing", headers=auth,
                       json={"lat": 28.46, "lng": 77.03})
    body = resp.json()
    assert resp.status_code == 200
    assert body["district"] == "Gurugram"
    assert body["city"] == "Delhi NCR"
    assert {"flood", "fire", "accident"} <= set(body["risks"])
    assert len(body["nearest_hospitals"]) > 0
    assert body["nearest_hospitals"][0]["hospital"] == "Medanta Gurugram"
    assert body["suggestions"] and body["ai_summary"]


def test_image_report_detects_hazards(client, auth):
    resp = client.post("/api/v1/incidents/report/image", headers=auth,
                       files={"file": ("cctv.jpg", b"demo-image-bytes", "image/jpeg")})
    body = resp.json()
    assert body["agent"] == "vision"
    assert body["data"]["hazards"]
