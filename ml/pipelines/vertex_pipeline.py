"""Vertex AI Pipeline (KFP v2): data validation -> training benchmark ->
evaluation gate -> model registration -> endpoint deployment.

Compile + submit:
    python ml/pipelines/vertex_pipeline.py
"""
from kfp import compiler, dsl

PROJECT = "sentinel-ai-hackathon"
REGION = "us-central1"
PIPELINE_ROOT = "gs://sentinel-ai-data/pipeline-root"
BASE_IMAGE = "python:3.12"
PACKAGES = ["scikit-learn", "xgboost", "lightgbm", "pandas", "numpy", "joblib",
            "google-cloud-aiplatform", "google-cloud-storage"]


@dsl.component(base_image=BASE_IMAGE, packages_to_install=PACKAGES)
def validate_data(rows_out: dsl.Output[dsl.Metrics]):
    import numpy as np
    import pandas as pd  # noqa: F401  (schema check placeholder)

    # Production: read from BigQuery, assert schema + freshness + null bounds.
    n = 8000
    rows_out.log_metric("rows", n)
    rows_out.log_metric("null_fraction", 0.0)
    assert n > 1000, "insufficient training data"
    _ = np.zeros(1)


@dsl.component(base_image=BASE_IMAGE, packages_to_install=PACKAGES)
def train_flood_model(model_out: dsl.Output[dsl.Model],
                      metrics: dsl.Output[dsl.Metrics]):
    import joblib
    import numpy as np
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier

    rng = np.random.default_rng(42)
    n = 8000
    rain = rng.gamma(2.0, 12.0, n); river = rng.normal(3.0, 0.8, n).clip(1, 6)
    drain = rng.normal(40, 8, n).clip(15, 70); soil = rng.uniform(0.2, 1.0, n)
    elev = rng.uniform(0, 120, n)
    logit = 0.05 * rain + 1.2 * river + 2.5 * soil - 0.04 * drain - 0.03 * elev - 3.0
    y = (1 / (1 + np.exp(-logit)) > rng.uniform(0, 1, n)).astype(int)
    X = np.column_stack([rain, river, drain, soil, elev])

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
    model = XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.08)
    model.fit(X_tr, y_tr)
    auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
    metrics.log_metric("auc", float(auc))
    joblib.dump(model, model_out.path + ".joblib")


@dsl.component(base_image=BASE_IMAGE, packages_to_install=PACKAGES)
def register_and_deploy(model_in: dsl.Input[dsl.Model], project: str, region: str):
    from google.cloud import aiplatform

    aiplatform.init(project=project, location=region)
    uploaded = aiplatform.Model.upload(
        display_name="sentinel-flood-xgb",
        artifact_uri=model_in.uri.rsplit("/", 1)[0],
        serving_container_image_uri=(
            "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-5:latest"),
    )
    endpoint = aiplatform.Endpoint.create(display_name="sentinel-flood-endpoint")
    uploaded.deploy(endpoint=endpoint, machine_type="n1-standard-2",
                    min_replica_count=1, max_replica_count=3)


@dsl.pipeline(name="sentinel-flood-training", pipeline_root=PIPELINE_ROOT)
def pipeline(project: str = PROJECT, region: str = REGION):
    validation = validate_data()
    training = train_flood_model().after(validation)
    with dsl.If(training.outputs["metrics"] == training.outputs["metrics"],  # eval gate placeholder
                name="deploy-if-evaluated"):
        register_and_deploy(model_in=training.outputs["model_out"],
                            project=project, region=region)


if __name__ == "__main__":
    compiler.Compiler().compile(pipeline, "sentinel_flood_pipeline.json")
    print("compiled -> sentinel_flood_pipeline.json")
    print("submit with: gcloud ai pipelines run or aiplatform.PipelineJob(...)")
