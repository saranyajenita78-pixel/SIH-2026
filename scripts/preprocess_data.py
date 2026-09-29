"""
scripts/preprocess_data.py
Runs the cleaning/preprocessing step against current weather data for both
stations and writes the cleaned output to data/processed/ (CSV), preserving
the original raw file untouched (per project ingestion policy).

Run:  python scripts/preprocess_data.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.pipeline import get_weather_for_station
from src.data.preprocessing import clean_weather
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    for station_id in config.STATIONS:
        raw_df, provenance = get_weather_for_station(station_id, scenario="NORMAL")
        cleaned = clean_weather(raw_df)
        out_path = os.path.join(config.PROCESSED_DIR, f"{station_id.lower()}_weather_processed.csv")
        cleaned.to_csv(out_path, index=False)
        logger.info("Wrote processed weather data for %s to %s (%d rows). Source: %s",
                    station_id, out_path, len(cleaned), provenance)
        print(f"[{station_id}] -> {out_path} ({len(cleaned)} rows)")


if __name__ == "__main__":
    main()
