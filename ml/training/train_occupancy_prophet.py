"""Hospital occupancy forecasting with Prophet (weekly seasonality).
Exports per-hospital 14-day forecasts to BigQuery for Looker dashboards."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.ml.synthetic import HOSPITALS, hospital_occupancy_series  # noqa: E402

OUT = Path(__file__).resolve().parent / "artifacts"
OUT.mkdir(exist_ok=True)


def main():
    from prophet import Prophet

    series = hospital_occupancy_series(days=180)
    forecasts = []
    for hospital in HOSPITALS:
        hist = (series[series["hospital"] == hospital]
                .rename(columns={"date": "ds", "occupancy": "y"}))
        model = Prophet(weekly_seasonality=True, daily_seasonality=False,
                        yearly_seasonality=False)
        model.fit(hist[["ds", "y"]])
        future = model.make_future_dataframe(periods=14)
        pred = model.predict(future).tail(14)
        pred["hospital"] = hospital
        forecasts.append(pred[["ds", "hospital", "yhat", "yhat_lower", "yhat_upper"]])
        print(f"{hospital}: day+14 occupancy {pred['yhat'].iloc[-1]:.2%}")

    result = pd.concat(forecasts, ignore_index=True)
    result.to_csv(OUT / "occupancy_forecast_prophet.csv", index=False)


if __name__ == "__main__":
    main()
