# Sentinel AI — Emergency Decision Intelligence Platform

> **"AI that predicts emergencies before they become disasters."**

Sentinel AI fuses a city's fragmented emergency data — weather, traffic,
hospitals, 911 calls, CCTV, citizen reports — into one continuously running
decision loop: **sense → predict → decide → act**, powered by Gemini 2.5 Pro,
a 10-agent mesh (Google ADK), and 7 ML models, with every decision explained
and audited.

Built for the Google Cloud GenAI Hackathon.

## Quick start (zero cloud credentials needed)

```bash
# backend (demo mode: full platform with mocked GCP clients)
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements-demo.txt
.venv/bin/python data/generators/generate.py          # synthetic city data
cd backend && ../.venv/bin/uvicorn app.main:app --port 8000

# frontend
cd frontend && npm install && npm run dev              # http://localhost:3000
```

Log in as `commander / command123` (also: admin, responder, hospital, citizen —
see [docs/api/API.md](docs/api/API.md)). Or run everything with
`docker compose up`.

```bash
cd backend && ../.venv/bin/python -m pytest            # 19 tests
```

## What it does

| Capability | How |
|---|---|
| **Multi-agent decisions** | 5 situational agents run in parallel every 5 min (Cloud Scheduler); a Decision Agent fuses them via confidence-weighted scoring + Gemini reasoning; a Workflow Agent auto-notifies hospitals/police/ambulance/citizens above P1 threshold |
| **Predictive ML** | Flood, accident, fire, severity classifiers (XGBoost/LightGBM/CatBoost benchmarked), hospital occupancy (Prophet), ambulance demand (LSTM), congestion — served via Vertex AI in prod |
| **Explainable AI** | Every prediction ships SHAP attributions + a plain-language narrative |
| **Multimodal intake** | Voice calls → Speech-to-Text → Gemini structuring; CCTV/drone images → Vision AI triage → Gemini scene analysis |
| **Grounded RAG** | SOP PDFs → Document AI → chunking → Vertex Embeddings → Vector Search → Gemini answers with citations |
| **Conversational AI** | Chat auto-routes between RAG, decision-cycle, and general Gemini modes |

## Repository map

```
backend/            FastAPI app (Cloud Run)
  app/agents/       10 agents + orchestrator + ADK app
  app/services/     GCP wrappers (real client + demo fallback each)
  app/ml/ app/xai/  prediction engine + SHAP explainer
  app/rag/          Document AI → Embeddings → Vector Search → Gemini
  app/db/           AlloyDB SQL, BigQuery DDL, Firestore collections
  tests/            unit + integration (19 tests)
frontend/           Next.js 15 + MUI dark dashboard (10 pages, Google Maps)
ml/                 offline training (XGB/LGBM/CatBoost/Prophet/LSTM) + Vertex Pipeline
functions/          Cloud Functions (Pub/Sub consumers)
data/               synthetic data + sample SOP PDFs + demo call audio
infra/terraform/    full GCP resource graph (APIs→AlloyDB→Vector Search→Scheduler→Monitoring)
docs/               architecture/sequence/ER diagrams, API docs, Postman,
                    Looker guide, business value, GCP justification,
                    presentation, demo script
.github/ cloudbuild.yaml   CI (tests+build) → CD (Cloud Build → Cloud Run)
```

## Architecture

See [docs/diagrams/architecture.md](docs/diagrams/architecture.md) (Mermaid).
25+ Google Cloud services; justification for each in
[docs/gcp_services_justification.md](docs/gcp_services_justification.md).

## Deploying to Google Cloud

```bash
cd infra/terraform && terraform init && terraform apply   # infra
gcloud builds submit --config cloudbuild.yaml .           # build + deploy
python data/generators/generate.py --bigquery             # seed warehouse
```

Set `DEMO_MODE=false` on Cloud Run; secrets (`JWT_SECRET`,
`GOOGLE_MAPS_API_KEY`) come from Secret Manager. GitHub Actions deploys on
push to `main` via Workload Identity Federation (no SA keys).

## Security

JWT auth · 5-role RBAC enforced per route · least-privilege service account
(Terraform) · Secret Manager · full audit trail (agent runs, notifications,
work orders) in Firestore/AlloyDB · structured Cloud Logging + custom
`sentinel/risk_score` metric with alert policies.

## Demo

Follow [docs/demo_script.md](docs/demo_script.md) — 7 minutes, works fully
offline in demo mode.
