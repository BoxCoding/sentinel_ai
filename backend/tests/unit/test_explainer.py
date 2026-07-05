from app.ml.predictors import engine
from app.xai.explainer import explain_prediction


def test_explanation_structure():
    prob, model, X = engine.flood_probability({
        "rain_6h_mm": 95, "river_level_m": 4.2, "drainage_capacity": 35,
        "soil_saturation": 0.9, "elevation_m": 8,
    })
    exp = explain_prediction(model, X, prob)
    assert set(exp) == {"probability", "top_factors", "all_factors", "narrative"}
    assert len(exp["top_factors"]) == 3
    assert exp["narrative"].startswith("Risk is")


def test_high_risk_factors_point_up():
    """For an extreme flood input, top factors should increase risk."""
    prob, model, X = engine.flood_probability({
        "rain_6h_mm": 120, "river_level_m": 5.0, "drainage_capacity": 20,
        "soil_saturation": 0.98, "elevation_m": 3,
    })
    exp = explain_prediction(model, X, prob)
    assert prob > 0.8
    assert exp["top_factors"][0]["attribution"] > 0
