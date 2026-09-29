"""
scripts/train_models.py
Trains and evaluates every ML model for both stations under the NORMAL
scenario, prints metrics, and logs a model_runs row in the database.

Run:  python scripts/train_models.py
"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.pipeline import run_full_pipeline
from src.database import db
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    db.initialize_database()
    result = run_full_pipeline(scenario="NORMAL")

    for station_id, sdata in result["stations"].items():
        print(f"\n=== {station_id} ===")

        print("Equipment anomaly detection (per unit):")
        for r in sdata["anomaly_results"]:
            print(f"  {r['equipment_id']}: health={r['health_pct']}%, "
                  f"anomaly_prob={r['anomaly_probability']}, priority={r['priority']}")

        if sdata["forecast_result"]:
            fr = sdata["forecast_result"]
            print("Energy forecast:")
            print(f"  Baseline: {fr['baseline_metrics']}")
            print(f"  Model:    {fr['model_metrics']}")
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO model_runs (model_name, trained_at, metrics_json, notes) "
                    "VALUES (?, ?, ?, ?)",
                    ("energy_forecast_random_forest", datetime.utcnow().isoformat(),
                     json.dumps({"station": station_id, "baseline": fr["baseline_metrics"],
                                 "model": fr["model_metrics"]}),
                     "Time-aware split; compared against previous-hour persistence baseline."),
                )
        else:
            print("Energy forecast: not enough history in this scenario window.")

    db.log_event("models_trained", "scripts/train_models.py run complete")
    print("\nModel training/evaluation complete. See database `model_runs` table for a log.")


if __name__ == "__main__":
    main()
