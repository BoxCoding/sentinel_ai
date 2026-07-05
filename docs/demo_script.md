# Demo Script (7 minutes)

**Setup (before judges arrive):** `docker compose up` or the two dev servers;
log in as `commander/command123`; keep a second tab on `/docs` (Swagger).

## 0:00 — Hook (30s)
> "Every city has the data to see a flood coming six hours early. None of them
> connect it. Sentinel AI is the decision layer that does."

## 0:30 — Home dashboard (1 min)
- Point at KPIs: 24 live emergency calls, 75% hospital occupancy.
- Click **RUN DECISION CYCLE**. While it runs: "Five specialist agents —
  weather, traffic, hospital, emergency, prediction — are analyzing the city in
  parallel right now."
- Gauge slams to **95% / P1-CRITICAL**. Read the fused decision aloud.

## 1:30 — Explainable prediction (1.5 min)
- Predictions page. Set rain to 95mm, river to 4.2m → **98% flood probability**.
- Show the XAI panel: "It's not a black box — rainfall, elevation and river
  level each carry a SHAP attribution, in plain language a commander can defend
  to the press."
- Drag rain down to 10mm → probability collapses. "Live counterfactuals."

## 3:00 — Multimodal intake (1.5 min)
- Swagger tab → `POST /incidents/report/voice`, upload `data/samples/audio` clip.
- Show the structured incident: Speech-to-Text transcript → Gemini extracted
  type=fire, address, severity=CRITICAL, geocoded.
- Same for a CCTV frame via `/incidents/report/image`: Vision AI + Gemini
  agree it's a flooded street, impassable to sedans.

## 4:30 — Grounded RAG (1 min)
- AI Chat: "What is the flood SOP activation protocol?"
- Show citations chips: "Answers come only from the city's own SOP documents —
  Document AI → Vertex Embeddings → Vector Search → Gemini. No hallucinated policy."

## 5:30 — Automation & audit (1 min)
- Timeline page: the P1 decision auto-notified hospitals, police, ambulance
  control and pushed a citizen advisory — every action logged.
- Log in as `admin` → Admin audit trail: "Gov-grade accountability."

## 6:30 — Close (30s)
- Architecture slide: 25+ Google Cloud services, Terraform'd, CI/CD via
  GitHub Actions + Cloud Build.
> "Reactive cities count casualties. Predictive cities prevent them.
> Sentinel AI makes prediction operational."

## Fallbacks
- No internet: everything shown runs in DEMO_MODE locally.
- Question "is the ML real?": open `backend/tests/` — 19 passing tests including
  monotonicity checks; `ml/training/train_models.py` benchmarks XGBoost/LightGBM/CatBoost.
