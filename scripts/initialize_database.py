"""
scripts/initialize_database.py
Creates the SQLite schema and seeds static reference data (stations,
equipment master list, data source registry). Safe to run multiple times.

Run:  python scripts/initialize_database.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.database import db
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Initializing database at %s", config.DATABASE_PATH)
    db.initialize_database()
    db.seed_stations()

    # Register the data sources this project uses/expects (see DATA_SOURCES.md)
    db.record_data_source(
        dataset_name="Station reference metadata (name, coordinates, region)",
        source_org="Public knowledge / REAL_REFERENCE",
        station_id=None,
        dataset_type="Reference",
        data_status=config.REAL_REFERENCE,
        access_status="Public",
        notes="Station coordinates and founding years are public reference facts, not sensor telemetry.",
    )
    for sid in config.STATIONS:
        db.record_data_source(
            dataset_name=f"{sid} Automatic Weather Station (AWS) data",
            source_org="NCPOR / National Polar Data Centre (NPDC)",
            station_id=sid,
            dataset_type="Meteorological",
            data_status=config.REAL_OBSERVED,
            access_status="Not fetched in this build environment (no outbound internet). "
                           "See src/data/ncpor_loader.py — drop a CSV export into "
                           "data/raw/ncpor/ to activate REAL_OBSERVED weather data.",
            notes="Falls back to SIMULATED_DEMO via src/data/simulator.py until a real export is supplied.",
        )
    db.record_data_source(
        dataset_name="Equipment / energy / inventory / logistics telemetry",
        source_org="Project simulator (src/data/simulator.py)",
        station_id=None,
        dataset_type="Operational (simulated)",
        data_status=config.SIMULATED_DEMO,
        access_status="N/A — not a real feed",
        notes="Deterministic, relationship-driven simulation. No real Antarctic station "
              "operational telemetry is publicly available for this project; see LIMITATIONS.md.",
    )

    db.log_event("database_initialized", "Schema created and reference data seeded.")
    logger.info("Database initialization complete.")


if __name__ == "__main__":
    main()
