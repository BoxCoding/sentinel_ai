# Looker Studio — Executive Dashboards

Data source: BigQuery dataset `sentinel_ai` (views defined in
`backend/app/db/bigquery_schema.sql`).

## Setup
1. Looker Studio → Create → Data source → BigQuery → `sentinel-ai-hackathon.sentinel_ai`.
2. Connect the three views below; enable owner's-credentials caching (15 min).
3. Import the page layout described here (one page per section).

## Pages & widgets

### 1. Command KPIs
- Scorecards: incidents today, avg response time, P1 decisions, citizens alerted
  — source `v_incident_trends` + `decision_cycles`.
- Time series: daily incidents by type (stacked), `v_incident_trends`.

### 2. Risk Heatmap
- Geo chart on district lat/lng, bubble color = `avg_risk`, source `v_risk_heatmap`
  filtered `model = 'flood'`; add model filter control (flood/fire/accident).
- Pivot: district x model peak risk.

### 3. Hospital Capacity
- Bar: `avg_occupancy` per hospital with 90% reference line, `v_hospital_occupancy`.
- Table: min ICU free, peak occupancy, conditional red formatting above 0.9.

### 4. Response Performance
- Time series: emergency response time (from `incidents_stream` ingested by the
  incident_processor Cloud Function).
- Scorecard with sparkline: 30-day trend vs 8-minute SLA target.

All charts filter by a global date-range and district control.
