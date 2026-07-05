from app.ml.predictors import engine
from app.ml.synthetic import HOSPITALS


def test_flood_probability_monotonic():
    high, _, _ = engine.flood_probability({
        "rain_6h_mm": 100, "river_level_m": 4.5, "drainage_capacity": 30,
        "soil_saturation": 0.95, "elevation_m": 5,
    })
    low, _, _ = engine.flood_probability({
        "rain_6h_mm": 5, "river_level_m": 2.0, "drainage_capacity": 60,
        "soil_saturation": 0.2, "elevation_m": 100,
    })
    assert 0 <= low < high <= 1
    assert high > 0.7 and low < 0.3


def test_fire_risk_bounds():
    prob, _, _ = engine.fire_risk({
        "temp_c": 42, "humidity": 0.15, "wind_kmh": 45,
        "building_age": 60, "industrial": 1,
    })
    assert 0 <= prob <= 1
    assert prob > 0.5


def test_severity_classifier_range():
    severity, proba = engine.emergency_severity({
        "injuries": 4, "trapped": 1, "spreading": 1, "vulnerable": 1, "etype": 1,
    })
    assert severity in (0, 1, 2, 3)
    assert severity >= 2  # multi-injury + trapped must not be LOW
    assert abs(sum(proba) - 1.0) < 1e-6


def test_hospital_forecast_shape():
    forecast = engine.hospital_occupancy_forecast(HOSPITALS[0], horizon_days=7)
    assert len(forecast) == 7
    assert all(0 <= f["predicted_occupancy"] <= 1 for f in forecast)


def test_ambulance_demand_deterministic():
    a = engine.ambulance_demand_forecast("Gurugram", 6)
    b = engine.ambulance_demand_forecast("Gurugram", 6)
    assert a == b
