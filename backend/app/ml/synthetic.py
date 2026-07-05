"""Synthetic training data generators. The same distributions are used by
data/generators for BigQuery seeding, so demo predictions look coherent
with the dashboards."""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

DISTRICTS = [
    # Delhi NCR
    "Connaught Place", "Gurugram", "Noida", "Dwarka", "Yamuna Bank",
    # Mumbai
    "Colaba", "Bandra", "Andheri", "Kurla", "Dadar",
    # Bengaluru
    "Koramangala", "Whitefield", "Indiranagar", "Bellandur", "Hebbal",
]
HOSPITALS = ["AIIMS Delhi", "Medanta Gurugram", "Fortis Noida",
             "Lilavati Mumbai", "KEM Mumbai",
             "Manipal Bengaluru", "St. John's Bengaluru"]


def flood_training_data(n: int = 4000) -> pd.DataFrame:
    rain_6h = RNG.gamma(2.0, 12.0, n)              # mm
    river_level = RNG.normal(3.0, 0.8, n).clip(1, 6)
    drainage_capacity = RNG.normal(40, 8, n).clip(15, 70)
    soil_saturation = RNG.uniform(0.2, 1.0, n)
    elevation_m = RNG.uniform(0, 120, n)
    logit = (0.05 * rain_6h + 1.2 * river_level + 2.5 * soil_saturation
             - 0.04 * drainage_capacity - 0.03 * elevation_m - 3.0)
    flood = (1 / (1 + np.exp(-logit)) > RNG.uniform(0, 1, n)).astype(int)
    return pd.DataFrame({
        "rain_6h_mm": rain_6h, "river_level_m": river_level,
        "drainage_capacity": drainage_capacity, "soil_saturation": soil_saturation,
        "elevation_m": elevation_m, "flood": flood,
    })


def accident_training_data(n: int = 4000) -> pd.DataFrame:
    congestion = RNG.uniform(0, 1, n)
    rain_mm = RNG.gamma(1.5, 8.0, n)
    hour = RNG.integers(0, 24, n)
    is_night = ((hour >= 22) | (hour <= 5)).astype(int)
    road_quality = RNG.uniform(0.3, 1.0, n)
    logit = 2.0 * congestion + 0.03 * rain_mm + 0.8 * is_night - 2.5 * road_quality - 0.5
    accident = (1 / (1 + np.exp(-logit)) > RNG.uniform(0, 1, n)).astype(int)
    return pd.DataFrame({
        "congestion": congestion, "rain_mm": rain_mm, "hour": hour,
        "is_night": is_night, "road_quality": road_quality, "accident": accident,
    })


def fire_training_data(n: int = 4000) -> pd.DataFrame:
    temp_c = RNG.normal(28, 8, n)
    humidity = RNG.uniform(0.1, 0.95, n)
    wind_kmh = RNG.gamma(2, 6, n)
    building_age = RNG.uniform(0, 80, n)
    industrial = RNG.integers(0, 2, n)
    logit = 0.06 * temp_c - 3.0 * humidity + 0.03 * wind_kmh + 0.015 * building_age + 0.9 * industrial - 2.2
    fire = (1 / (1 + np.exp(-logit)) > RNG.uniform(0, 1, n)).astype(int)
    return pd.DataFrame({
        "temp_c": temp_c, "humidity": humidity, "wind_kmh": wind_kmh,
        "building_age": building_age, "industrial": industrial, "fire": fire,
    })


def hospital_occupancy_series(days: int = 120) -> pd.DataFrame:
    """Daily occupancy % per hospital with weekly seasonality — used for
    forecasting (Prophet offline; exponential-smoothing in-process)."""
    frames = []
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    for hospital_idx, hospital in enumerate(HOSPITALS):
        base = 0.60 + 0.04 * hospital_idx
        weekly = 0.06 * np.sin(2 * np.pi * np.arange(days) / 7)
        trend = np.linspace(0, 0.05, days)
        noise = RNG.normal(0, 0.03, days)
        occupancy = (base + weekly + trend + noise).clip(0.3, 0.99)
        frames.append(pd.DataFrame({"date": dates, "hospital": hospital, "occupancy": occupancy}))
    return pd.concat(frames, ignore_index=True)


def severity_training_data(n: int = 3000) -> pd.DataFrame:
    """Emergency severity from structured call features (0=low..3=critical)."""
    injuries = RNG.poisson(0.8, n)
    trapped = RNG.integers(0, 2, n)
    spreading = RNG.integers(0, 2, n)
    vulnerable = RNG.integers(0, 2, n)  # children/elderly involved
    etype = RNG.integers(0, 5, n)       # 0 medical,1 fire,2 flood,3 accident,4 other
    score = injuries + 2 * trapped + 1.5 * spreading + vulnerable + (etype == 1) * 0.5
    severity = np.digitize(score, [1, 2.5, 4])
    return pd.DataFrame({
        "injuries": injuries, "trapped": trapped, "spreading": spreading,
        "vulnerable": vulnerable, "etype": etype, "severity": severity,
    })
