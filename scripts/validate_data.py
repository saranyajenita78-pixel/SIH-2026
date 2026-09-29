"""
scripts/validate_data.py
Runs validation checks against the current pipeline output for both stations
and prints a report. Useful as a pre-demo sanity check.

Run:  python scripts/validate_data.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_full_pipeline
from src.data.data_validator import validate_dataframe
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

WEATHER_REQUIRED = ["station_id", "timestamp", "temperature_c", "wind_speed_kmh"]
EQUIPMENT_REQUIRED = ["equipment_id", "timestamp", "temperature_c", "vibration_mm_s"]


def main():
    result = run_full_pipeline(scenario="NORMAL")
    any_issues = False

    for station_id, sdata in result["stations"].items():
        print(f"\n--- {station_id} ---")

        is_valid, issues = validate_dataframe(sdata["weather_df"], WEATHER_REQUIRED)
        print(f"Weather data valid: {is_valid}")
        for i in issues:
            print(f"  - {i}")
            any_issues = True

        is_valid, issues = validate_dataframe(sdata["equipment_df"], EQUIPMENT_REQUIRED,
                                              range_overrides={"temperature_c": (-40, 150)})
        print(f"Equipment data valid: {is_valid}")
        for i in issues:
            print(f"  - {i}")
            any_issues = True

    print("\n" + ("Some non-blocking data-quality notes were found above." if any_issues
                   else "All datasets passed validation with no issues."))


if __name__ == "__main__":
    main()
