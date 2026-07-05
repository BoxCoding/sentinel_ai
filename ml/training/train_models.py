"""Offline training: benchmarks XGBoost / LightGBM / CatBoost / RandomForest
on each prediction task, exports the winner to GCS for Vertex AI serving.

    python ml/training/train_models.py [--upload]
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.ml import synthetic  # noqa: E402

OUT = Path(__file__).resolve().parent / "artifacts"
OUT.mkdir(exist_ok=True)

TASKS = {
    "flood": (synthetic.flood_training_data, "flood"),
    "accident": (synthetic.accident_training_data, "accident"),
    "fire": (synthetic.fire_training_data, "fire"),
}


def candidates():
    models = {"random_forest": RandomForestClassifier(n_estimators=300, max_depth=10,
                                                      random_state=42, n_jobs=-1)}
    try:
        from xgboost import XGBClassifier
        models["xgboost"] = XGBClassifier(n_estimators=300, max_depth=5,
                                          learning_rate=0.08, eval_metric="auc")
    except ImportError:
        print("xgboost not installed; skipping")
    try:
        from lightgbm import LGBMClassifier
        models["lightgbm"] = LGBMClassifier(n_estimators=300, max_depth=6,
                                            learning_rate=0.08, verbose=-1)
    except ImportError:
        print("lightgbm not installed; skipping")
    try:
        from catboost import CatBoostClassifier
        models["catboost"] = CatBoostClassifier(iterations=300, depth=6,
                                                learning_rate=0.08, verbose=False)
    except ImportError:
        print("catboost not installed; skipping")
    return models


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action="store_true", help="Upload winners to GCS")
    args = parser.parse_args()

    report = {}
    for task, (loader, target) in TASKS.items():
        df = loader(n=8000)
        X, y = df.drop(columns=target), df[target]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25,
                                                  random_state=42, stratify=y)
        scores = {}
        best_name, best_model, best_auc = None, None, -1.0
        for name, model in candidates().items():
            model.fit(X_tr, y_tr)
            auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
            scores[name] = round(auc, 4)
            if auc > best_auc:
                best_name, best_model, best_auc = name, model, auc
        joblib.dump(best_model, OUT / f"{task}_{best_name}.joblib")
        report[task] = {"scores": scores, "winner": best_name, "auc": round(best_auc, 4)}
        print(f"{task}: {scores} -> winner {best_name} (AUC {best_auc:.4f})")

    (OUT / "benchmark_report.json").write_text(json.dumps(report, indent=2))

    if args.upload:
        from google.cloud import storage as gcs

        from app.core.config import settings

        bucket = gcs.Client(project=settings.GCP_PROJECT_ID).bucket(settings.GCS_BUCKET)
        for artifact in OUT.glob("*.joblib"):
            bucket.blob(f"models/{artifact.name}").upload_from_filename(artifact)
            print(f"uploaded gs://{settings.GCS_BUCKET}/models/{artifact.name}")


if __name__ == "__main__":
    main()
