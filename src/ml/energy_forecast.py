"""
src/ml/energy_forecast.py
Short-horizon energy consumption forecasting.

Two models are trained and compared, per the project's ML methodology
(always compare against a baseline):
    1. BASELINE: moving average of the last N hours (naive persistence-style)
    2. MODEL:    RandomForestRegressor on lag + rolling + hour-of-day features

Time-aware split is used (train on the past, test on the most recent block) —
never a random shuffle — to avoid leaking future information into training.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

LAGS = [1, 2, 3, 6, 24]


def _build_features(df):
    df = df.copy().reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    for lag in LAGS:
        df[f"lag_{lag}"] = df["consumption_kw"].shift(lag)
    df["roll_mean_6"] = df["consumption_kw"].rolling(6, min_periods=1).mean().shift(1)
    df = df.dropna().reset_index(drop=True)
    return df


def train_and_evaluate(energy_df, test_fraction=0.2):
    """
    Returns dict with baseline + model metrics, fitted model, and a dataframe
    of (timestamp, actual, baseline_pred, model_pred) for the test window —
    ready for plotting Actual / Predicted / Forecast range.
    """
    feat_df = _build_features(energy_df)
    n = len(feat_df)
    split = int(n * (1 - test_fraction))
    train, test = feat_df.iloc[:split], feat_df.iloc[split:]

    feature_cols = [f"lag_{l}" for l in LAGS] + ["roll_mean_6", "hour"]
    X_train, y_train = train[feature_cols], train["consumption_kw"]
    X_test, y_test = test[feature_cols], test["consumption_kw"]

    # --- Baseline: previous-hour persistence ---
    baseline_pred = test["lag_1"].values

    # --- Model ---
    model = RandomForestRegressor(
        n_estimators=100, max_depth=8, random_state=config.SIM_RANDOM_SEED
    )
    model.fit(X_train, y_train)
    model_pred = model.predict(X_test)

    # Refit on all available historical rows for the actual next-hour forecast.
    final_model = RandomForestRegressor(
        n_estimators=100, max_depth=8, random_state=config.SIM_RANDOM_SEED
    )
    final_model.fit(feat_df[feature_cols], feat_df["consumption_kw"])
    next_hour_prediction = predict_next_hour(final_model, energy_df, feature_cols)

    def metrics(y_true, y_pred):
        return {
            "MAE": round(float(mean_absolute_error(y_true, y_pred)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
            "R2": round(float(r2_score(y_true, y_pred)), 3),
        }

    result_df = pd.DataFrame({
        "timestamp": test["timestamp"].values,
        "actual_kw": y_test.values,
        "baseline_pred_kw": baseline_pred,
        "model_pred_kw": model_pred,
    })

    return {
        "model": final_model,
        "feature_cols": feature_cols,
        "next_hour_prediction_kw": round(next_hour_prediction, 2),
        "baseline_metrics": metrics(y_test, baseline_pred),
        "model_metrics": metrics(y_test, model_pred),
        "result_df": result_df,
        "data_status": config.MODEL_PREDICTION,
    }


def load_saved_model(station_id):
    """Load the pre-trained normal-operation energy model artifact."""
    import joblib
    path = os.path.join(config.MODELS_DIR, f"{station_id.lower()}_energy_forecast.joblib")
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def fast_forecast(energy_df, station_id):
    """Use the saved artifact instead of retraining during every dashboard load.

    The artifact was trained offline on SIMULATED_DEMO operational telemetry.
    Current scenario data is used only to construct the next-hour feature vector.
    """
    bundle = load_saved_model(station_id)
    if not bundle or len(energy_df) < max(LAGS) + 1:
        return None
    model = bundle["model"]
    feature_cols = bundle.get("feature_cols") or [f"lag_{l}" for l in LAGS] + ["roll_mean_6", "hour"]
    next_pred = predict_next_hour(model, energy_df, feature_cols)

    # Compact recent-series chart: no retraining, only inference.
    df = energy_df.copy().reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    feat = _build_features(df)
    recent = feat.tail(min(24, len(feat))).copy()
    if recent.empty:
        result_df = pd.DataFrame(columns=["timestamp", "actual_kw", "baseline_pred_kw", "model_pred_kw"])
    else:
        preds = model.predict(recent[feature_cols])
        result_df = pd.DataFrame({
            "timestamp": recent["timestamp"].values,
            "actual_kw": recent["consumption_kw"].values,
            "baseline_pred_kw": recent["lag_1"].values,
            "model_pred_kw": preds,
        })
    return {
        "model": model,
        "feature_cols": feature_cols,
        "next_hour_prediction_kw": round(next_pred, 2),
        "baseline_metrics": bundle.get("baseline_metrics", {}),
        "model_metrics": bundle.get("model_metrics", {}),
        "result_df": result_df,
        "data_status": config.MODEL_PREDICTION,
        "training_note": "Metrics from the saved normal-operation SIMULATED_DEMO training artifact; current chart is inference only.",
    }


def predict_next_hour(model, energy_df, feature_cols=None):
    """Predict the next hourly consumption value from the latest known history."""
    feature_cols = feature_cols or [f"lag_{l}" for l in LAGS] + ["roll_mean_6", "hour"]
    df = energy_df.copy().reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if len(df) < max(LAGS) + 1:
        raise ValueError("At least 25 hourly observations are required for next-hour forecasting")
    x = {}
    for lag in LAGS:
        x[f"lag_{lag}"] = float(df["consumption_kw"].iloc[-lag])
    x["roll_mean_6"] = float(df["consumption_kw"].tail(6).mean())
    x["hour"] = int((df["timestamp"].iloc[-1] + pd.Timedelta(hours=1)).hour)
    X = pd.DataFrame([x])[feature_cols]
    return float(model.predict(X)[0])
