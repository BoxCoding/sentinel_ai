# Sentinel AI — Hackathon Presentation (12 slides)

---
## 1. Sentinel AI
**Emergency Decision Intelligence Platform**
*"AI that predicts emergencies before they become disasters."*
Team · Google Cloud GenAI Hackathon

---
## 2. The Problem
- Emergency management is **reactive**: cities respond after the damage starts.
- 9 data streams (calls, CCTV, weather, traffic, hospitals, social, GPS…) — **zero integration**.
- Commanders can't answer in real time: *Which hospital overloads next? Where do ambulances go? What's the top priority right now?*

---
## 3. The Insight
The data to predict most urban emergencies **already exists**.
What's missing is a **decision layer**: fuse, predict, explain, act.

---
## 4. What We Built
A 10-agent AI mesh on Google Cloud that every 5 minutes:
**senses** (weather/traffic/hospital/calls/vision/voice) →
**predicts** (7 ML models) → **decides** (Gemini fusion, risk+confidence+reasoning) →
**acts** (auto-notify, work orders, citizen alerts) — all **explainable and audited**.

---
## 5. Live Demo
(dashboard → decision cycle → 95% P1-CRITICAL → XAI flood what-if →
voice call intake → RAG with citations → automated workflow audit)

---
## 6. Multi-Agent Architecture (Google ADK)
Weather · Traffic · Hospital · Emergency · Vision · Voice · RAG · Prediction
→ **Decision Agent** (weighted confidence fusion + Gemini action plan)
→ **Workflow Agent** (notifications, work orders, reports)

---
## 7. AI Capabilities Coverage
Conversational ✓ RAG ✓ Multimodal ✓ Vision ✓ Audio ✓ Predictive ML ✓
Forecasting ✓ Recommendations ✓ Workflow automation ✓ **Explainable AI ✓**
(every score ships SHAP factors + plain-language narrative)

---
## 8. Google Cloud Stack (25+ services)
Gemini 2.5 Pro · Vertex AI (Embeddings, Vector Search, Pipelines, Endpoints) ·
BigQuery · Firestore · AlloyDB · Pub/Sub · Cloud Run · Functions · Scheduler ·
Document AI · Speech/TTS · Vision AI · Maps · Looker Studio ·
IAM · Secret Manager · Logging · Monitoring · Cloud Build · GitHub Actions

---
## 9. ML That Holds Up
- 7 models: flood, accident, fire, severity, occupancy (Prophet), demand (LSTM), congestion
- Benchmarked XGBoost vs LightGBM vs CatBoost per task (AUC-gated)
- Vertex AI Pipelines: validate → train → eval gate → register → deploy
- 19 automated tests incl. monotonicity + RBAC + end-to-end API flow

---
## 10. Impact (2M-population city, modeled)
- **6–12h** flood warning lead time (was ~0)
- **15%** faster dispatch → 120+ lives/year
- **30%** fewer hospital-door diversions
- < **$1,500/mo** steady-state cloud cost (scale-to-zero)

---
## 11. Production-Ready, Not a Prototype
Clean architecture · JWT + RBAC (5 roles) · full audit trail ·
Terraform IaC · CI/CD (Actions + Cloud Build) · Docker ·
demo mode runs the entire platform offline

---
## 12. Ask & Roadmap
Pilot with one district EOC this flood season →
citizen mobile app (Firestore offline) → multilingual voice (TTS) →
GCP Marketplace listing.
**Reactive cities count casualties. Predictive cities prevent them.**
