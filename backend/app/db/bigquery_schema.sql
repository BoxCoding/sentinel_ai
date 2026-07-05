-- Sentinel AI — BigQuery analytics warehouse (dataset: sentinel_ai)
-- Historical telemetry + ML features. Looker Studio reads these tables
-- and the views at the bottom.

CREATE SCHEMA IF NOT EXISTS `sentinel_ai`
OPTIONS (location = "us-central1");

CREATE TABLE IF NOT EXISTS `sentinel_ai.weather_current` (
  district STRING NOT NULL, lat FLOAT64, lng FLOAT64, elevation_m FLOAT64,
  rain_6h_mm FLOAT64, river_level_m FLOAT64, drainage_capacity FLOAT64,
  soil_saturation FLOAT64, temp_c FLOAT64, humidity FLOAT64, wind_kmh FLOAT64,
  observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) PARTITION BY DATE(observed_at);

CREATE TABLE IF NOT EXISTS `sentinel_ai.traffic_sensors` (
  road STRING NOT NULL, district STRING, congestion_index FLOAT64,
  avg_speed_kmh FLOAT64, vehicle_count_15m INT64,
  observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) PARTITION BY DATE(observed_at);

CREATE TABLE IF NOT EXISTS `sentinel_ai.road_closures` (
  road STRING NOT NULL, district STRING, reason STRING, closed_since TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `sentinel_ai.hospital_status` (
  hospital STRING NOT NULL, district STRING, lat FLOAT64, lng FLOAT64,
  total_beds INT64, occupancy FLOAT64, icu_beds_free INT64,
  doctors_on_duty INT64, medicine_stock_days FLOAT64, ambulances_available INT64,
  observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) PARTITION BY DATE(observed_at);

CREATE TABLE IF NOT EXISTS `sentinel_ai.emergency_calls` (
  call_id STRING NOT NULL, type STRING, district STRING, lat FLOAT64, lng FLOAT64,
  description STRING, injuries INT64, trapped INT64, spreading INT64,
  vulnerable INT64, received_at TIMESTAMP
) PARTITION BY DATE(received_at);

CREATE TABLE IF NOT EXISTS `sentinel_ai.citizen_reports` (
  report_id STRING NOT NULL, district STRING, channel STRING,
  text STRING, reported_at TIMESTAMP
) PARTITION BY DATE(reported_at);

CREATE TABLE IF NOT EXISTS `sentinel_ai.predictions_log` (
  model STRING NOT NULL, entity STRING, probability FLOAT64,
  features JSON, explanation JSON,
  predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) PARTITION BY DATE(predicted_at);

CREATE TABLE IF NOT EXISTS `sentinel_ai.decision_cycles` (
  cycle_id STRING NOT NULL, risk_score FLOAT64, priority STRING,
  summary STRING, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) PARTITION BY DATE(created_at);

-- ---------- Looker Studio views ----------
CREATE OR REPLACE VIEW `sentinel_ai.v_incident_trends` AS
SELECT DATE(received_at) AS day, type, district, COUNT(*) AS calls,
       SUM(injuries) AS injuries
FROM `sentinel_ai.emergency_calls`
GROUP BY day, type, district;

CREATE OR REPLACE VIEW `sentinel_ai.v_hospital_occupancy` AS
SELECT hospital, district,
       AVG(occupancy) AS avg_occupancy,
       MAX(occupancy) AS peak_occupancy,
       MIN(icu_beds_free) AS min_icu_free
FROM `sentinel_ai.hospital_status`
GROUP BY hospital, district;

CREATE OR REPLACE VIEW `sentinel_ai.v_risk_heatmap` AS
SELECT entity AS district, model,
       AVG(probability) AS avg_risk, MAX(probability) AS peak_risk,
       DATE(predicted_at) AS day
FROM `sentinel_ai.predictions_log`
WHERE model IN ('flood','fire','accident')
GROUP BY district, model, day;
