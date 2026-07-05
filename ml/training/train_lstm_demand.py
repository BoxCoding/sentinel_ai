"""Ambulance demand forecasting with an LSTM (Keras). Hourly call volume per
district; 24-step lookback predicting the next 6 hours."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

OUT = Path(__file__).resolve().parent / "artifacts"
OUT.mkdir(exist_ok=True)
LOOKBACK, HORIZON = 24, 6


def synthetic_hourly_demand(days: int = 90) -> np.ndarray:
    rng = np.random.default_rng(11)
    hours = days * 24
    t = np.arange(hours)
    daily = 3 + 1.5 * np.sin(2 * np.pi * (t % 24 - 14) / 24)   # afternoon peak
    weekly = 0.5 * np.sin(2 * np.pi * t / (24 * 7))
    return np.clip(daily + weekly + rng.normal(0, 0.4, hours), 0.2, None)


def make_windows(series: np.ndarray):
    X, y = [], []
    for i in range(len(series) - LOOKBACK - HORIZON):
        X.append(series[i:i + LOOKBACK])
        y.append(series[i + LOOKBACK:i + LOOKBACK + HORIZON])
    return np.array(X)[..., None], np.array(y)


def main():
    from tensorflow import keras

    series = synthetic_hourly_demand()
    X, y = make_windows(series)
    split = int(len(X) * 0.8)

    model = keras.Sequential([
        keras.layers.Input(shape=(LOOKBACK, 1)),
        keras.layers.LSTM(64, return_sequences=True),
        keras.layers.LSTM(32),
        keras.layers.Dense(HORIZON),
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(X[:split], y[:split], validation_data=(X[split:], y[split:]),
              epochs=15, batch_size=64, verbose=2)
    model.save(OUT / "ambulance_demand_lstm.keras")
    mae = model.evaluate(X[split:], y[split:], verbose=0)[1]
    print(f"val MAE: {mae:.3f} calls/hour")


if __name__ == "__main__":
    main()
