"""
src/data/data_validator.py
Validation checks applied to any dataframe before it enters the database:
column presence, timestamp parseability, numeric range sanity and duplicate
detection. Used for both real (NCPOR) and simulated data.
"""

import pandas as pd

VALID_RANGES = {
    "temperature_c": (-90, 20),
    "humidity_pct": (0, 100),
    "pressure_hpa": (850, 1085),
    "wind_speed_kmh": (0, 350),
    "vibration_mm_s": (0, 50),
    "load_pct": (0, 100),
    "fuel_level_pct": (0, 100),
}


def validate_dataframe(df, required_columns, range_overrides=None):
    """Returns (is_valid, list_of_issues).
    range_overrides: optional dict to override/extend VALID_RANGES for
    columns whose meaning differs by context (e.g. 'temperature_c' means
    ambient air temperature in weather data, but equipment operating
    temperature in equipment_readings — these need different bounds)."""
    issues = []

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")
        return False, issues

    if "timestamp" in df.columns:
        try:
            pd.to_datetime(df["timestamp"])
        except Exception as exc:
            issues.append(f"Unparseable timestamps: {exc}")

    ranges = dict(VALID_RANGES)
    if range_overrides:
        ranges.update(range_overrides)

    for col, (lo, hi) in ranges.items():
        if col in df.columns:
            bad = df[(df[col] < lo) | (df[col] > hi)]
            if len(bad) > 0:
                issues.append(f"{len(bad)} out-of-range values in '{col}' "
                              f"(expected [{lo}, {hi}])")

    na_counts = df.isna().sum()
    for col, cnt in na_counts.items():
        if cnt > 0:
            issues.append(f"{cnt} missing values in '{col}'")

    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append(f"{dup_count} duplicate rows detected")

    is_valid = not any("Missing required columns" in i or "Unparseable" in i for i in issues)
    return is_valid, issues
