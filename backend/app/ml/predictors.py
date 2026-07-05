"""In-process prediction engine.

Production path: models are trained offline (ml/training/*), registered in the
Vertex AI Model Registry via Vertex AI Pipelines, and served on Vertex
endpoints. This module keeps functionally identical sklearn models trained on
the same synthetic distributions so every API works in demo mode, and exposes
predict_proba-compatible objects to the SHAP explainer either way."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

from app.core.logging import get_logger
from app.ml import synthetic

log = get_logger(__name__)
MODEL_DIR = Path(__file__).resolve().parent / ".model_cache"
MODEL_DIR.mkdir(exist_ok=True)


class PredictionEngine:
    def __init__(self):
        self._models: dict[str, object] = {}

    @staticmethod
    def _attach_stats(model, X: pd.DataFrame, y: pd.Series):
        """Feature stats used by the XAI fallback when SHAP is unavailable:
        mean/std for normalization, target correlation for direction."""
        model.feature_names_ = list(X.columns)
        model.feature_means_ = X.mean().to_dict()
        model.feature_stds_ = X.std().replace(0, 1).to_dict()
        model.feature_corr_ = {c: float(np.corrcoef(X[c], y)[0, 1]) for c in X.columns}
        return model

    def _get(self, name: str, trainer):
        if name in self._models:
            return self._models[name]
        cache = MODEL_DIR / f"{name}.joblib"
        if cache.exists():
            self._models[name] = joblib.load(cache)
        else:
            log.info("training_model", model=name)
            self._models[name] = trainer()
            joblib.dump(self._models[name], cache)
        return self._models[name]

    # ---------------- trainers ----------------
    def _train_flood(self):
        df = synthetic.flood_training_data()
        model = GradientBoostingClassifier(n_estimators=150, max_depth=4, random_state=42)
        X, y = df.drop(columns="flood"), df["flood"]
        model.fit(X, y)
        return self._attach_stats(model, X, y)

    def _train_accident(self):
        df = synthetic.accident_training_data()
        model = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42)
        X, y = df.drop(columns="accident"), df["accident"]
        model.fit(X, y)
        return self._attach_stats(model, X, y)

    def _train_fire(self):
        df = synthetic.fire_training_data()
        model = GradientBoostingClassifier(n_estimators=150, max_depth=4, random_state=42)
        X, y = df.drop(columns="fire"), df["fire"]
        model.fit(X, y)
        return self._attach_stats(model, X, y)

    def _train_severity(self):
        df = synthetic.severity_training_data()
        model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
        X, y = df.drop(columns="severity"), df["severity"]
        model.fit(X, y)
        return self._attach_stats(model, X, y)

    # ---------------- public API ----------------
    def flood_probability(self, features: dict) -> tuple[float, object, pd.DataFrame]:
        model = self._get("flood", self._train_flood)
        X = pd.DataFrame([features])[model.feature_names_]
        return float(model.predict_proba(X)[0, 1]), model, X

    def accident_probability(self, features: dict) -> tuple[float, object, pd.DataFrame]:
        model = self._get("accident", self._train_accident)
        X = pd.DataFrame([features])[model.feature_names_]
        return float(model.predict_proba(X)[0, 1]), model, X

    def fire_risk(self, features: dict) -> tuple[float, object, pd.DataFrame]:
        model = self._get("fire", self._train_fire)
        X = pd.DataFrame([features])[model.feature_names_]
        return float(model.predict_proba(X)[0, 1]), model, X

    def emergency_severity(self, features: dict) -> tuple[int, np.ndarray]:
        model = self._get("severity", self._train_severity)
        X = pd.DataFrame([features])[model.feature_names_]
        return int(model.predict(X)[0]), model.predict_proba(X)[0]

    def hospital_occupancy_forecast(self, hospital: str, horizon_days: int = 7) -> list[dict]:
        """Holt-style exponential smoothing with weekly seasonality (Prophet
        equivalent runs offline in ml/training/train_occupancy_prophet.py)."""
        series = synthetic.hospital_occupancy_series()
        hist = series[series["hospital"] == hospital].sort_values("date")
        if hist.empty:
            return []
        values = hist["occupancy"].to_numpy()
        level = values[-14:].mean()
        weekly = np.array([values[i::7][-4:].mean() - values[-28:].mean() for i in range(7)])
        trend = (values[-7:].mean() - values[-14:-7].mean()) / 7
        last_date = hist["date"].max()
        out = []
        for day in range(1, horizon_days + 1):
            forecast = float(np.clip(level + trend * day + weekly[day % 7], 0, 1))
            out.append({
                "date": (last_date + pd.Timedelta(days=day)).date().isoformat(),
                "hospital": hospital,
                "predicted_occupancy": round(forecast, 3),
                "overload_risk": forecast > 0.90,
            })
        return out

    def ambulance_demand_forecast(self, district: str, horizon_hours: int = 12) -> list[dict]:
        rng = np.random.default_rng(abs(hash(district)) % (2**32))
        base = rng.uniform(2, 6)
        now_hour = pd.Timestamp.now().hour
        out = []
        for h in range(horizon_hours):
            hour = (now_hour + h) % 24
            rush = 1.4 if hour in (8, 9, 17, 18, 19) else 1.0
            night = 0.7 if 1 <= hour <= 5 else 1.0
            out.append({
                "hour_offset": h, "district": district,
                "expected_calls": round(base * rush * night, 1),
            })
        return out

    def traffic_congestion_forecast(self, district: str, horizon_hours: int = 6) -> list[dict]:
        rng = np.random.default_rng(abs(hash("traffic" + district)) % (2**32))
        now_hour = pd.Timestamp.now().hour
        out = []
        for h in range(horizon_hours):
            hour = (now_hour + h) % 24
            peak = 0.85 if hour in (8, 9, 17, 18, 19) else 0.45
            out.append({
                "hour_offset": h, "district": district,
                "congestion_index": round(float(np.clip(peak + rng.normal(0, 0.08), 0, 1)), 2),
            })
        return out


engine = PredictionEngine()
