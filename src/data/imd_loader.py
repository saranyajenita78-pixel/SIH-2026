"""IMD Polar WRF / Antarctic forecast ingestion.

IMD publishes Polar WRF forecasts for Maitri and Bharati.  The public site
currently does not expose a stable documented machine-readable API for these
products, so this adapter intentionally accepts an official CSV/JSON export
rather than pretending an undocumented endpoint is an API.
"""

import json
import os
import pandas as pd

import config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

COLUMN_ALIASES = {
    "timestamp": ["timestamp", "valid_time", "datetime", "date_time", "time", "forecast_time"],
    "temperature_c": ["temperature_c", "temperature", "temp", "temp_c", "t2m", "2m_temperature"],
    "humidity_pct": ["humidity_pct", "humidity", "relative_humidity", "rh", "rh2m"],
    "pressure_hpa": ["pressure_hpa", "pressure", "mslp", "slp", "surface_pressure"],
    "wind_speed_kmh": ["wind_speed_kmh", "wind_speed", "windspeed", "ws", "wind_kmh"],
    "wind_dir_deg": ["wind_dir_deg", "wind_direction", "wind_dir", "wd"],
}

REQUIRED_COLUMNS = ["timestamp"]


def _find_file(station_id):
    station = station_id.lower()
    for ext in ("csv", "json"):
        exact = os.path.join(config.RAW_IMD_DIR, f"{station}_polar_wrf.{ext}")
        if os.path.exists(exact):
            return exact
    for name in os.listdir(config.RAW_IMD_DIR):
        if station in name.lower() and name.lower().endswith((".csv", ".json")):
            return os.path.join(config.RAW_IMD_DIR, name)
    return None


def _map_columns(df):
    lower_cols = {str(c).lower().strip(): c for c in df.columns}
    rename_map = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                rename_map[lower_cols[alias]] = target
                break
    return df.rename(columns=rename_map)


def load_station_forecast(station_id):
    path = _find_file(station_id)
    if path is None:
        return None, {
            "found": False,
            "message": f"No official IMD Polar WRF export found for {station_id}. "
                       f"Place it at data/raw/imd/{station_id.lower()}_polar_wrf.csv (or .json).",
        }
    try:
        if path.lower().endswith(".json"):
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            raw = pd.DataFrame(payload if isinstance(payload, list) else payload.get("data", payload))
        else:
            raw = pd.read_csv(path)
    except Exception as exc:
        return None, {"found": True, "message": f"IMD forecast file could not be parsed: {exc}"}

    df = _map_columns(raw)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, {"found": True, "message": f"IMD forecast file is missing required columns: {missing}"}

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    for col in ("temperature_c", "humidity_pct", "pressure_hpa", "wind_speed_kmh", "wind_dir_deg"):
        if col not in df.columns:
            df[col] = None
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # IMD Polar WRF source products commonly report wind speed in knots. If a
    # file explicitly says wind_speed_knots, convert it before standardising.
    if "wind_speed_knots" in raw.columns and "wind_speed_kmh" not in raw.columns:
        df["wind_speed_kmh"] = pd.to_numeric(raw["wind_speed_knots"], errors="coerce") * 1.852

    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    df["station_id"] = station_id
    df["source"] = "IMD Polar WRF"
    df["data_status"] = config.REAL_FORECAST
    keep = ["station_id", "timestamp", "temperature_c", "humidity_pct",
            "pressure_hpa", "wind_speed_kmh", "wind_dir_deg", "source", "data_status"]
    return df[keep], {
        "found": True,
        "message": f"Loaded {len(df)} IMD Polar WRF forecast rows from {os.path.basename(path)}.",
        "path": path,
    }
