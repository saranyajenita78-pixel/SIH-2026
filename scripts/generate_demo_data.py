"""
scripts/generate_demo_data.py
Runs the full pipeline for the NORMAL scenario and persists a snapshot into
the database tables (weather_readings, equipment_readings, energy_readings,
inventory, logistics, communication_status, predictions, alerts,
recommendations). The Streamlit dashboard recomputes live on each Demo Mode
change; this script exists so the database is populated immediately after
`setup.bat`, and so `python app.py`-less inspection (e.g. via DB Browser for
SQLite) shows real rows right away.

Run:  python scripts/generate_demo_data.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.database import db
from src.pipeline import run_full_pipeline
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def persist_snapshot(scenario="NORMAL"):
    result = run_full_pipeline(scenario=scenario)

    for table in ("weather_readings", "equipment_readings", "energy_readings",
                  "inventory", "logistics", "communication_status", "alerts",
                  "recommendations"):
        db.clear_table(table)

    for station_id, sdata in result["stations"].items():
        db.bulk_insert_df("weather_readings", sdata["weather_df"])
        db.bulk_insert_df("equipment_readings", sdata["equipment_df"])
        db.bulk_insert_df("energy_readings", sdata["energy_df"])
        db.bulk_insert_df("inventory", sdata["inventory_df"])
        db.bulk_insert_df("logistics", sdata["logistics_df"])

        import pandas as pd
        db.bulk_insert_df("communication_status", pd.DataFrame([sdata["communication"]]))

        if sdata["alerts"]:
            db.bulk_insert_df("alerts", pd.DataFrame(sdata["alerts"]))
        if sdata["recommendations"]:
            db.bulk_insert_df("recommendations", pd.DataFrame(sdata["recommendations"]))

        logger.info("Persisted snapshot for %s (%s scenario): %d weather rows, "
                    "%d equipment rows, %d alerts",
                    station_id, scenario, len(sdata["weather_df"]),
                    len(sdata["equipment_df"]), len(sdata["alerts"]))

    db.log_event("demo_data_generated", f"scenario={scenario}")


def main():
    db.initialize_database()
    db.seed_stations()
    persist_snapshot("NORMAL")
    logger.info("Demo data generation complete.")


if __name__ == "__main__":
    main()
