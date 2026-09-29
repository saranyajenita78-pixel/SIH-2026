"""Build inspectable ML artifacts for the prototype.

These artifacts are trained on the project's clearly labelled synthetic
operational telemetry because authorised Antarctic equipment telemetry is not
public. Runtime scenario evaluation still retrains on the current scenario.
The saved artifacts make the models directory auditable and reproducible.
"""
import json
import os
import sys
from datetime import datetime, timezone
import joblib
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.data import simulator
from src.ml import anomaly_detection, energy_forecast


def main():
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "training_data": "SIMULATED_DEMO operational telemetry",
        "reason": "Internal station equipment/energy telemetry is not publicly available.",
        "runtime_note": "Dashboard uses the compact selected-scenario pipeline; artifacts are retained for audit/reproducibility.",
        "artifacts": [],
    }

    for station_id in config.STATIONS:
        weather = simulator.generate_weather(station_id, scenario="NORMAL")
        equipment_frames = [
            simulator.generate_equipment(eq, weather, scenario="NORMAL")
            for eq in config.EQUIPMENT_LIST if eq["station"] == station_id
        ]
        equipment_df = pd.concat(equipment_frames, ignore_index=True)
        anomaly_models = anomaly_detection.train_equipment_anomaly_model(equipment_df)
        anomaly_path = os.path.join(config.MODELS_DIR, f"{station_id.lower()}_equipment_anomaly.joblib")
        joblib.dump(anomaly_models, anomaly_path, compress=3)
        manifest["artifacts"].append({"file": os.path.basename(anomaly_path), "type": "IsolationForest + z-score baseline"})

        energy_df = simulator.generate_energy(station_id, weather, scenario="NORMAL")
        energy_result = energy_forecast.train_and_evaluate(energy_df)
        energy_path = os.path.join(config.MODELS_DIR, f"{station_id.lower()}_energy_forecast.joblib")
        joblib.dump({
            "model": energy_result["model"],
            "feature_cols": energy_result["feature_cols"],
            "baseline_metrics": energy_result["baseline_metrics"],
            "model_metrics": energy_result["model_metrics"],
        }, energy_path, compress=3)
        manifest["artifacts"].append({"file": os.path.basename(energy_path), "type": "RandomForestRegressor energy forecast"})

    with open(os.path.join(config.MODELS_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"Created {len(manifest['artifacts'])} model artifacts in {config.MODELS_DIR}")


if __name__ == "__main__":
    main()
