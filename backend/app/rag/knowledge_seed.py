"""Seed knowledge base: condensed emergency SOPs indexed at startup so the
RAG agent answers meaningfully out of the box. Full PDFs live in
data/samples/pdfs and can be re-ingested via POST /api/v1/rag/ingest."""
from app.rag.pipeline import rag

SEED_DOCUMENTS = {
    "flood_response_sop.md": """
FLOOD RESPONSE STANDARD OPERATING PROCEDURE — City Disaster Management Authority.
Activation levels: Level 1 (advisory) when 6-hour rainfall exceeds 50mm. Level 2
(alert) when rainfall exceeds 80mm or river gauge reaches 4.0m. Level 3 (emergency)
when river gauge exceeds 4.5m danger mark or flooding is reported in 3+ wards.
At Level 2: pre-position rescue boats at Yamuna Bank, Kurla and Bellandur
stations, open designated shelters, and issue push advisories to low-lying
districts (Yamuna Bank, Kurla, Andheri, Bellandur, Gurugram sector roads).
At Level 3: activate the Emergency Operations Center, deploy NDRF liaison,
suspend traffic on Minto Bridge Underpass and Andheri Subway, and begin
evacuation of ground-floor residences in flood zone A. Hospitals must shift
ground-floor patients and verify generator fuel for 72 hours.
""",
    "hospital_surge_protocol.md": """
HOSPITAL SURGE CAPACITY PROTOCOL. Occupancy above 85% triggers surge review;
above 90% the hospital must activate surge mode: discharge-ready patients are
processed within 4 hours, elective procedures are postponed, and the city
bed-management cell redirects non-critical ambulance traffic to the nearest
hospital under 80% occupancy. ICU overflow pairs: AIIMS Delhi <-> Fortis Noida;
Medanta Gurugram -> AIIMS Delhi; Lilavati Mumbai <-> KEM Mumbai;
Manipal Bengaluru <-> St. John's Bengaluru. Mass-casualty incidents trigger
the START triage protocol; each receiving hospital reports bed status every 30
minutes to the EOC.
""",
    "fire_safety_manual.md": """
FIRE RESPONSE MANUAL. Structure fires: first-due engine within 8 minutes for
90% of calls. Working fire (visible flame, occupied structure) requires 3 engines,
1 ladder, 1 rescue, and a battalion chief. Persons-reported fires escalate to
CRITICAL severity and dispatch an additional ambulance. Industrial-zone fires
require the hazmat unit on the first alarm. Wind above 30 km/h with humidity
under 30% raises the citywide fire risk index; open burning is prohibited and
brush patrols are doubled.
""",
    "ambulance_dispatch_guidelines.md": """
AMBULANCE DISPATCH GUIDELINES. Target response: 8 minutes urban, 15 minutes
peripheral. Deployment is demand-based: units reposition hourly using the
ambulance demand forecast. Each district keeps minimum coverage of 2 units;
Gurugram, Connaught Place, Andheri and Koramangala require 4 during rush hours
(08:00-10:00, 17:00-20:00). During flood alerts, ambulances avoid Minto Bridge
Underpass, Andheri Subway and Silk Board Junction and use elevated corridors.
Patients are routed per the hospital surge protocol —
never transport to a hospital above 90% occupancy except for immediate
life threats when it is the nearest facility.
""",
    "citizen_alert_policy.md": """
CITIZEN ALERT POLICY. Alerts are tiered: ADVISORY (informational, app push),
WARNING (act soon — push + SMS to affected wards), EMERGENCY (act now — push,
SMS, TV/radio break-in, siren activation). Emergency alerts require EOC commander
approval unless automated criteria are met: flood probability above 90%,
confirmed dam release, or a hazmat plume model intersecting a residential zone.
All alerts are logged with issuing authority, timestamp, affected zones, and
message text for post-incident audit.
""",
}


def seed_knowledge_base() -> int:
    total = 0
    for name, text in SEED_DOCUMENTS.items():
        result = rag.ingest_text(name, text.strip())
        total += result["chunks"]
    return total
