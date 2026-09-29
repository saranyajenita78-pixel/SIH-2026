"""
src/ml/anomaly_detection.py
Equipment anomaly detection for predictive maintenance.

Approach (deliberately simple + explainable, per project methodology: no deep
learning unless justified):

1. For each equipment unit, learn a BASELINE (mean/std per feature) from the
   earlier `baseline_fraction` of its own history — i.e. "known-good"
   behaviour — never the full series, so a slow-building anomaly cannot get
   absorbed into the model's own definition of "normal".
2. The primary anomaly score is a smoothed multivariate z-score (RMS of
   per-feature z-scores across a short trailing window) against that
   baseline. This is transparent and numerically stable, and its
   explanation is literally "which feature deviated most from this unit's
   own recent normal, and by how much" — ideal for the "why did the model
   detect it" requirement.
3. An IsolationForest trained on the same baseline is used as a secondary,
   independent CONFIRMATION flag (does an unsupervised ensemble model also
   consider this reading unusual?), reported alongside the primary score.

Because no ground-truth failure labels exist for this simulated telemetry,
evaluation is limited to these unsupervised diagnostics rather than
precision/recall — this limitation is stated explicitly in MODEL_CARD.md.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

FEATURES = ["temperature_c", "vibration_mm_s", "load_pct", "voltage_v"]


def train_equipment_anomaly_model(equipment_readings_df, baseline_fraction=0.6):
    """
    Learns a baseline per equipment_id: feature means/stds plus a fitted
    IsolationForest, both trained ONLY on the earlier `baseline_fraction` of
    that unit's history.
    Returns dict: equipment_id -> {means, stds, iso_model}
    """
    models = {}
    for eq_id, grp in equipment_readings_df.groupby("equipment_id"):
        grp = grp.sort_values("timestamp")
        cutoff = max(20, int(len(grp) * baseline_fraction))
        baseline = grp.iloc[:cutoff]
        X = baseline[FEATURES].fillna(baseline[FEATURES].mean())
        if len(X) < 20:
            continue

        means = X.mean()
        stds = X.std().replace(0, 1)

        iso_model = IsolationForest(
            n_estimators=80,
            max_samples=min(256, len(X)),
            contamination=config.ANOMALY_CONTAMINATION,
            random_state=config.SIM_RANDOM_SEED,
        )
        iso_model.fit(X)

        models[eq_id] = {"means": means, "stds": stds, "iso_model": iso_model}
    return models


def score_latest(equipment_readings_df, models, smoothing_window=6):
    """
    Scores the trailing `smoothing_window` readings per equipment unit.
    Returns a list of dicts with:
      - anomaly_probability (0-1, primary z-score-derived risk)
      - health_pct
      - priority (LOW/MEDIUM/HIGH/CRITICAL)
      - iso_forest_flag (secondary independent confirmation, bool)
      - top_signals (explainability: which features deviate most, and how)
    """
    results = []
    for eq_id, grp in equipment_readings_df.groupby("equipment_id"):
        grp = grp.sort_values("timestamp")
        bundle = models.get(eq_id)
        if bundle is None:
            continue
        means, stds, iso_model = bundle["means"], bundle["stds"], bundle["iso_model"]

        window = grp.iloc[-smoothing_window:]
        latest = grp.iloc[-1]

        # --- Primary score: smoothed multivariate z-score vs this unit's baseline ---
        z_window = (window[FEATURES] - means) / stds
        combined_z_per_row = np.sqrt((z_window ** 2).mean(axis=1))  # RMS across features
        combined_z = float(combined_z_per_row.mean())               # smoothed over window

        # Map RMS z-score to a 0-1 anomaly probability: z<=1 (within ~1 std,
        # jointly) is treated as normal noise; risk ramps up smoothly beyond that.
        anomaly_prob = float(np.clip(1 - np.exp(-max(0.0, combined_z - 1.0) / 1.5), 0, 1))
        health_pct = round((1 - anomaly_prob) * 100, 1)

        # --- Explainability: which single feature deviates most right now ---
        z_latest = {f: float((latest[f] - means[f]) / stds[f]) for f in FEATURES}
        top_signals = sorted(z_latest.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]

        # --- Secondary independent confirmation ---
        x_latest = pd.DataFrame([latest[FEATURES].astype(float).values], columns=FEATURES)
        iso_flag = bool(iso_model.predict(x_latest)[0] == -1)

        if anomaly_prob >= 0.75:
            priority = "CRITICAL"
        elif anomaly_prob >= 0.5:
            priority = "HIGH"
        elif anomaly_prob >= 0.25:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        results.append({
            "equipment_id": eq_id,
            "timestamp": latest["timestamp"],
            "health_pct": health_pct,
            "anomaly_probability": round(anomaly_prob, 3),
            "iso_forest_flag": iso_flag,
            "priority": priority,
            "top_signals": [
                {"feature": f, "z_score": round(z, 2),
                 "direction": "above normal" if z > 0 else "below normal"}
                for f, z in top_signals
            ],
            "data_status": config.MODEL_PREDICTION,
        })
    return results


def load_saved_model(station_id):
    """Load the inspectable normal-operation artifact when available."""
    import joblib
    path = os.path.join(config.MODELS_DIR, f"{station_id.lower()}_equipment_anomaly.joblib")
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None
