"""Explainable AI: SHAP feature attributions for every tree-model prediction,
translated into plain-language reasons for decision makers."""
import numpy as np
import pandas as pd

from app.core.logging import get_logger

log = get_logger(__name__)

FEATURE_DESCRIPTIONS = {
    "rain_6h_mm": "rainfall in the last 6 hours",
    "river_level_m": "current river level",
    "drainage_capacity": "district drainage capacity",
    "soil_saturation": "soil saturation",
    "elevation_m": "district elevation",
    "congestion": "traffic congestion level",
    "rain_mm": "current rainfall",
    "hour": "time of day",
    "is_night": "night-time driving conditions",
    "road_quality": "road surface quality",
    "temp_c": "ambient temperature",
    "humidity": "relative humidity",
    "wind_kmh": "wind speed",
    "building_age": "average building age",
    "industrial": "industrial land use",
}


def explain_prediction(model, X: pd.DataFrame, probability: float) -> dict:
    """Return SHAP attributions + a human-readable explanation."""
    try:
        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        # binary classifiers may return [neg, pos] — take the positive class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        values = np.array(shap_values).reshape(-1)[: len(X.columns)]
    except Exception as exc:  # SHAP optional at runtime; degrade to importances
        log.warning("shap_unavailable", error=str(exc))
        # Direction-aware fallback: importance x target-correlation sign x
        # z-score of the feature vs its training distribution.
        importances = getattr(model, "feature_importances_", np.ones(len(X.columns)))
        means = getattr(model, "feature_means_", {})
        stds = getattr(model, "feature_stds_", {})
        corr = getattr(model, "feature_corr_", {})
        values = np.array([
            imp * np.sign(corr.get(col, 1.0))
            * (X.iloc[0][col] - means.get(col, 0)) / stds.get(col, 1)
            for col, imp in zip(X.columns, importances)
        ])

    contributions = sorted(
        ({"feature": col, "value": round(float(X.iloc[0][col]), 3),
          "attribution": round(float(v), 4)}
         for col, v in zip(X.columns, values)),
        key=lambda c: abs(c["attribution"]), reverse=True,
    )
    top = contributions[:3]
    phrases = []
    for c in top:
        desc = FEATURE_DESCRIPTIONS.get(c["feature"], c["feature"])
        direction = "increases" if c["attribution"] > 0 else "decreases"
        phrases.append(f"{desc} ({c['value']}) {direction} risk")
    return {
        "probability": round(probability, 3),
        "top_factors": top,
        "all_factors": contributions,
        "narrative": (
            f"Risk is {probability:.0%} primarily because " + "; ".join(phrases) + "."
        ),
    }
