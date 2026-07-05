# Google Cloud Services — Why Each One

| Service | Role in Sentinel AI | Why this service (vs alternatives) |
|---|---|---|
| **Gemini 2.5 Pro** | Decision reasoning, multimodal scene analysis, call extraction, RAG answers | Only model needed for text+image+audio+PDF in one API; 1M context fits full agent briefings |
| **Gemini 2.5 Flash** | High-volume ADK sub-agent calls | 10x cheaper for routing/classification where Pro is overkill |
| **Vertex AI** | Model registry, endpoints, experiment tracking | Managed serving with autoscaling; IAM-integrated, no k8s to run |
| **Vertex AI Embeddings** | SOP chunk + query embeddings (text-embedding-005) | Task-typed embeddings (RETRIEVAL_DOCUMENT/QUERY) boost recall |
| **Vertex AI Vector Search** | Knowledge-base ANN index | Stream-updated index; sub-10ms neighbors at city-scale corpus |
| **Vertex AI Pipelines** | Train→eval→register→deploy for 3 risk models | Reproducible, scheduled retraining with eval gates |
| **BigQuery** | Telemetry warehouse, ML features, Looker source | Serverless, partitioned; SQL views feed Looker with zero ETL |
| **Cloud Storage** | Media uploads, SOP PDFs, model artifacts, embeddings delta | Versioned KB bucket doubles as Vector Search staging |
| **Cloud Run** | Backend + frontend serving | Scale-to-zero between incidents; burst to 1000 QPS during disasters |
| **Cloud Functions** | Pub/Sub consumers (incident→BQ, alert escalation) | Event-driven glue without keeping the main service hot |
| **Pub/Sub** | Event bus (incidents/alerts/workflows) | Decouples agents from consumers; replays for audit |
| **Firestore** | Live operational state | Real-time listeners for the incident board; offline-tolerant citizen app later |
| **Cloud Scheduler** | 5-minute decision cycle, nightly retrain trigger | Cron with OIDC auth into Cloud Run |
| **AlloyDB** | Users, work orders, audit (transactional) | Postgres-compatible with 4x OLTP throughput; columnar engine for audit analytics |
| **Looker Studio** | Executive KPIs, trends, heatmaps | Zero-cost sharing with city leadership; direct BQ views |
| **Google Maps API** | Emergency routing, geocoding, dashboard map | TRAFFIC_AWARE_OPTIMAL routing avoids flooded segments |
| **ADK** | Conversational multi-agent coordinator | First-class Gemini agent framework; deploys to Agent Engine/Cloud Run |
| **Document AI** | SOP PDF parsing for RAG | Layout-aware extraction beats naive text dumps for tables in manuals |
| **Speech-to-Text** | Emergency call transcription | Telephony model tuned for noisy 8kHz call audio |
| **Text-to-Speech** | Citizen alert broadcasts, IVR callbacks | Multi-language voices for public alerts |
| **Vision AI** | Fast hazard triage of CCTV frames | Cheap first-pass filter before Gemini deep analysis |
| **Cloud Logging/Monitoring** | Structured logs, custom risk_score metric, 5xx alerts | Ops without extra vendors; audit requirement for gov |
| **IAM + Secret Manager** | Least-privilege SA, JWT/API secrets | No keys in code; WIF from GitHub Actions |
| **Cloud Build + GitHub Actions** | CI (tests) + CD (build/deploy) | Actions for OSS-friendly CI; Cloud Build for in-VPC image builds |
