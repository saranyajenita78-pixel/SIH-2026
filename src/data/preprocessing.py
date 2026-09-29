"""
src/data/preprocessing.py
Cleaning / normalization applied after validation and before the data reaches
the database. Never overwrites the original raw file (see ingestion policy).
"""

import pandas as pd


def clean_weather(df):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp")
    df = df.drop_duplicates(subset=["station_id", "timestamp"])

    numeric_cols = ["temperature_c", "humidity_pct", "pressure_hpa",
                     "wind_speed_kmh", "wind_dir_deg"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].interpolate(limit_direction="both")

    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df


def add_rolling_features(df, value_col, windows=(3, 6, 24)):
    """Adds rolling mean/std features used by downstream ML models."""
    df = df.copy().reset_index(drop=True)
    for w in windows:
        df[f"{value_col}_roll_mean_{w}"] = df[value_col].rolling(w, min_periods=1).mean()
        df[f"{value_col}_roll_std_{w}"] = df[value_col].rolling(w, min_periods=1).std().fillna(0)
    df[f"{value_col}_delta"] = df[value_col].diff().fillna(0)
    return df
