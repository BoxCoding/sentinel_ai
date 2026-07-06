# Demo Video Script — 3:00 cut

Condensed from [demo_script.md](demo_script.md) (the 7-minute full walkthrough)
for a hackathon submission video. Record in one take with QuickTime
(Cmd+Shift+5) or Loom, then paste the resulting link at the bottom of this
file and in the [README](../README.md#demo-video).

**Before recording:**
- Both servers running: `./scripts/dev.sh` (or your two dev servers).
- `backend/.env` has `GEMINI_API_KEY` set so the AI badges show **connected**
  and Chat/Location give real answers, not canned text.
- Logged out, browser at `/login`, window sized ~1440×900, zoom reset.
- Have a second tab ready at `/docs` (Swagger) for the multimodal beat.
- Silence notifications; close unrelated tabs.

---

## 0:00–0:15 — Hook (15s)
*(Sitting on the login screen)*
> "Cities have all the data to see a disaster coming hours early — weather,
> traffic, hospitals, 911 calls. None of it talks to each other. Sentinel AI
> is the decision layer that connects it, in real time, across Delhi NCR,
> Mumbai and Bengaluru."

Log in as `commander / command123`.

## 0:15–0:50 — Live dashboard + decision cycle (35s)
- Point at the two status chips: **"Weather: LIVE (Open-Meteo)"** and
  **"AI: gemini-3.5-flash connected"**. *"This isn't mocked — that's a real
  weather feed and a real Gemini model talking to each other."*
- Click **RUN DECISION CYCLE**. *"Five agents — weather, traffic, hospital,
  emergency, prediction — just ran in parallel across three metros."*
- Gauge lands on a priority (e.g., P2/P1). Read the one-line summary aloud.

## 0:50–1:25 — My Location AI briefing (35s)
- Click **My Location** (allow geolocation, or tap a city button).
- *"It geolocates you to the nearest district — here, Gurugram — pulls live
  weather, runs the flood/fire/accident models, and Gemini writes the
  briefing: current conditions, nearest hospitals with real occupancy, and
  concrete safety suggestions. Not a template — generated live."*

## 1:25–1:55 — Explainable prediction (30s)
- Predictions page. Drag rainfall to ~95mm, river to ~4.2m → probability
  spikes. *"Every number ships an explanation — rainfall, river level,
  drainage each carry a factor a commander can defend to the press."*
- Drag rainfall back down — probability collapses. *"Live counterfactuals,
  not a black box."*

## 1:55–2:25 — Map + grounded chat (30s)
- Emergency Map: click **Mumbai** filter — real street tiles, markers snap in.
- AI Chat: ask *"What is the flood SOP activation protocol?"* — answer comes
  back with citation chips. *"Grounded in the city's own SOP documents via
  Vertex-style RAG — not hallucinated policy."*

## 2:25–2:50 — Automation & audit (25s)
- Timeline page: *"A P1 decision auto-notifies hospitals, police, ambulance
  control, and pushes a citizen advisory — every action logged."*
- Admin audit trail (quick flash): *"Full accountability trail, gov-grade."*

## 2:50–3:00 — Close (10s)
> "Reactive cities count casualties. Predictive cities prevent them.
> This is Sentinel AI."

---

## Video link
`<paste your recorded video link here>`
