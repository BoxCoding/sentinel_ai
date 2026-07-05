"""Demo data generator: writes the synthetic operational tables that back
demo mode (data/samples/*.csv) and can seed BigQuery in production:

    python data/generators/generate.py            # local CSVs
    python data/generators/generate.py --bigquery # also load into BigQuery

Covers three metros: Delhi NCR (incl. Gurugram, Noida), Mumbai, Bengaluru.
NOTE: elevation_m is RELATIVE elevation above the local river/drainage level
(0-120 scale), not absolute altitude — it feeds the flood model directly.
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "samples"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(7)

# Shared geography lives in the backend so live feeds and synthetic data
# can never drift apart.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.core.geography import DISTRICT_META, HOSPITAL_META  # noqa: E402

DISTRICTS = {name: (m["city"], m["lat"], m["lng"], m["relative_elev_m"], m["flood_prone"])
             for name, m in DISTRICT_META.items()}
HOSPITALS = {name: (m["city"], m["district"], m["lat"], m["lng"], m["beds"])
             for name, m in HOSPITAL_META.items()}

ROADS = {
    "NH-48 Delhi-Gurugram": "Gurugram", "Ring Road": "Connaught Place",
    "DND Flyway": "Noida", "Dwarka Expressway": "Dwarka",
    "Western Express Highway": "Andheri", "Eastern Express Highway": "Kurla",
    "SV Road": "Bandra", "Marine Drive": "Colaba",
    "Outer Ring Road": "Bellandur", "Old Airport Road": "Indiranagar",
    "Hosur Road": "Koramangala", "Bellary Road": "Hebbal",
}
CONGESTED_ROADS = {"NH-48 Delhi-Gurugram", "Western Express Highway",
                   "Outer Ring Road", "Ring Road"}

CALL_TYPES = ["medical", "fire", "flood", "accident", "other"]
CALL_DESCRIPTIONS = {
    "medical": "Chest pain reported, patient conscious",
    "fire": "Smoke visible from building, possible structure fire",
    "flood": "Street waterlogged, vehicles stranded",
    "accident": "Two-vehicle collision, injuries reported",
    "other": "Public disturbance reported",
}


def weather_current() -> pd.DataFrame:
    rows = []
    for district, (city, lat, lng, elev, flood_prone) in DISTRICTS.items():
        # monsoon scenario: Mumbai heaviest, flood-prone districts saturated
        monsoon = {"Mumbai": 1.5, "Delhi NCR": 1.0, "Bengaluru": 0.9}[city]
        rain = float(RNG.gamma(6, 13) * monsoon) if flood_prone else float(RNG.gamma(2, 8) * monsoon)
        rows.append({
            "district": district, "city": city, "lat": lat, "lng": lng,
            "elevation_m": elev,
            "rain_6h_mm": round(rain, 1),
            "river_level_m": round(4.1 if flood_prone else RNG.uniform(2.2, 3.2), 2),
            "drainage_capacity": round(float(RNG.normal(33 if flood_prone else 48, 5)), 1),
            "soil_saturation": round(float(RNG.uniform(0.75, 0.95) if flood_prone
                                           else RNG.uniform(0.3, 0.6)), 2),
            "temp_c": round(float(RNG.normal({"Mumbai": 30, "Delhi NCR": 34, "Bengaluru": 26}[city], 2)), 1),
            "humidity": round(float(RNG.uniform(0.7, 0.95) if city == "Mumbai"
                                    else RNG.uniform(0.45, 0.8)), 2),
            "wind_kmh": round(float(RNG.gamma(3, 8)), 1),
        })
    return pd.DataFrame(rows)


def traffic_sensors() -> pd.DataFrame:
    rows = []
    for road, district in ROADS.items():
        city = DISTRICTS[district][0]
        congestion = (float(RNG.uniform(0.65, 0.95)) if road in CONGESTED_ROADS
                      else float(RNG.uniform(0.25, 0.6)))
        rows.append({
            "road": road, "district": district, "city": city,
            "congestion_index": round(congestion, 2),
            "avg_speed_kmh": round(60 * (1 - congestion), 1),
            "vehicle_count_15m": int(RNG.integers(80, 1200)),
        })
    return pd.DataFrame(rows)


def road_closures() -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    return pd.DataFrame([
        {"road": "Minto Bridge Underpass", "district": "Connaught Place", "city": "Delhi NCR",
         "reason": "Waterlogging under bridge", "closed_since": (now - timedelta(hours=3)).isoformat()},
        {"road": "Andheri Subway", "district": "Andheri", "city": "Mumbai",
         "reason": "Monsoon flooding", "closed_since": (now - timedelta(hours=5)).isoformat()},
        {"road": "Silk Board Junction", "district": "Koramangala", "city": "Bengaluru",
         "reason": "Storm drain overflow", "closed_since": (now - timedelta(hours=2)).isoformat()},
    ])


def hospital_status() -> pd.DataFrame:
    rows = []
    high_load = {"AIIMS Delhi", "KEM Mumbai", "St. John's Bengaluru"}
    for hospital, (city, district, lat, lng, beds) in HOSPITALS.items():
        occupancy = (float(RNG.uniform(0.84, 0.94)) if hospital in high_load
                     else float(RNG.uniform(0.55, 0.8)))
        rows.append({
            "hospital": hospital, "city": city, "district": district,
            "lat": lat, "lng": lng,
            "total_beds": beds, "occupancy": round(occupancy, 2),
            "icu_beds_free": int(RNG.integers(0, 15)),
            "doctors_on_duty": int(beds * RNG.uniform(0.04, 0.08)),
            "medicine_stock_days": round(float(RNG.uniform(1.5, 14)), 1),
            "ambulances_available": int(RNG.integers(1, 10)),
        })
    return pd.DataFrame(rows)


def emergency_calls(n: int = 36) -> pd.DataFrame:
    rows = []
    now = datetime.now(timezone.utc)
    names = list(DISTRICTS)
    for i in range(n):
        ctype = str(RNG.choice(CALL_TYPES, p=[0.35, 0.15, 0.15, 0.25, 0.10]))
        district = str(RNG.choice(names))
        city, lat, lng, _, _ = DISTRICTS[district]
        rows.append({
            "call_id": f"CALL-{1000 + i}", "type": ctype,
            "district": district, "city": city,
            "lat": round(lat + float(RNG.normal(0, 0.008)), 5),
            "lng": round(lng + float(RNG.normal(0, 0.008)), 5),
            "description": CALL_DESCRIPTIONS[ctype],
            "injuries": int(RNG.poisson(0.9)),
            "trapped": int(RNG.random() < 0.12),
            "spreading": int(ctype in ("fire", "flood") and RNG.random() < 0.4),
            "vulnerable": int(RNG.random() < 0.25),
            "received_at": (now - timedelta(minutes=int(RNG.integers(1, 360)))).isoformat(),
        })
    return pd.DataFrame(rows)


def citizen_reports(n: int = 60) -> pd.DataFrame:
    templates = ["Water entering ground floor near {d}", "Loud crash heard on {d} main road",
                 "Smoke smell in {d}", "Traffic signal down in {d}", "Tree fallen in {d}"]
    rows = []
    names = list(DISTRICTS)
    for i in range(n):
        district = str(RNG.choice(names))
        rows.append({
            "report_id": f"CR-{2000 + i}", "district": district,
            "city": DISTRICTS[district][0],
            "channel": str(RNG.choice(["app", "social", "sms"])),
            "text": str(RNG.choice(templates)).format(d=district),
            "reported_at": (datetime.now(timezone.utc)
                            - timedelta(minutes=int(RNG.integers(1, 720)))).isoformat(),
        })
    return pd.DataFrame(rows)


TABLES = {
    "weather_current": weather_current,
    "traffic_sensors": traffic_sensors,
    "road_closures": road_closures,
    "hospital_status": hospital_status,
    "emergency_calls": emergency_calls,
    "citizen_reports": citizen_reports,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bigquery", action="store_true",
                        help="Also load tables into BigQuery")
    args = parser.parse_args()

    for name, fn in TABLES.items():
        df = fn()
        path = OUT / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"wrote {path} ({len(df)} rows)")

    if args.bigquery:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
        from google.cloud import bigquery

        from app.core.config import settings

        client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        for name in TABLES:
            table_id = f"{settings.GCP_PROJECT_ID}.{settings.BQ_DATASET}.{name}"
            job = client.load_table_from_dataframe(
                pd.read_csv(OUT / f"{name}.csv"), table_id,
                job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
            )
            job.result()
            print(f"loaded {table_id}")


if __name__ == "__main__":
    main()
