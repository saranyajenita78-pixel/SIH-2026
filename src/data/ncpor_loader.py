"""
src/data/ncpor_loader.py
Ingestion layer for real NCPOR / National Polar Data Centre exports.

USAGE:
    Place a CSV export from the NCPOR / NPDC portal into:
        data/raw/ncpor/<station>_aws.csv
    Expected columns (case-insensitive, flexible order):
        timestamp, temperature_c, humidity_pct, pressure_hpa,
        wind_speed_kmh, wind_dir_deg
    (Column-name variants such as 'temp', 'temperature', 'wind_speed' etc.
    are auto-mapped where unambiguous — see COLUMN_ALIASES.)

    Run: python scripts/ingest_ncpor_data.py

If no local export is found, the loader attempts the public NCPOR/NPDC live
station page. It caches the last successful REAL_OBSERVED reading for
connectivity resilience. The loader never fabricates a downloaded file.
"""

import os
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.logging_config import get_logger
from src.data import ncpor_live

logger = get_logger(__name__)

COLUMN_ALIASES = {
    "timestamp": ["timestamp", "date", "datetime", "date_time", "time"],
    "temperature_c": ["temperature_c", "temperature", "temp", "temp_c", "air_temperature"],
    "humidity_pct": ["humidity_pct", "humidity", "relative_humidity", "rh"],
    "pressure_hpa": ["pressure_hpa", "pressure", "atm_pressure", "slp"],
    "wind_speed_kmh": ["wind_speed_kmh", "wind_speed", "windspeed", "ws"],
    "wind_dir_deg": ["wind_dir_deg", "wind_direction", "wind_dir", "wd"],
}

REQUIRED_COLUMNS = ["timestamp", "temperature_c"]


def _find_ncpor_file(station_id):
    fname_guess = f"{station_id.lower()}_aws.csv"
    path = os.path.join(config.RAW_NCPOR_DIR, fname_guess)
    if os.path.exists(path):
        return path
    # fall back to any csv containing the station name
    for f in os.listdir(config.RAW_NCPOR_DIR):
        if station_id.lower() in f.lower() and f.lower().endswith(".csv"):
            return os.path.join(config.RAW_NCPOR_DIR, f)
    return None


def _map_columns(df):
    lower_cols = {c.lower().strip(): c for c in df.columns}
    rename_map = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                rename_map[lower_cols[alias]] = target
                break
    return df.rename(columns=rename_map)



def _cache_dir():
    path = os.path.join(config.PROCESSED_DIR, "ncpor_cache")
    os.makedirs(path, exist_ok=True)
    return path

def _cache_path(station_id):
    return os.path.join(_cache_dir(), f"{station_id.lower()}_latest.csv")

def _save_cache(df, station_id):
    try:
        df.to_csv(_cache_path(station_id), index=False)
    except Exception as exc:
        logger.warning("Could not cache NCPOR data for %s: %s", station_id, exc)

def _load_cache(station_id):
    path = _cache_path(station_id)
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except Exception as exc:
        logger.warning("Could not read NCPOR cache for %s: %s", station_id, exc)
        return None

def load_station_weather(station_id):
    """
    Returns (dataframe_or_None, status_dict).
    status_dict describes whether a real file was found/usable, for logging
    and for the Data Explorer page's provenance banner.
    """
    path = _find_ncpor_file(station_id)
    if path is None:
        if config.NCPOR_LIVE_ENABLED:
            try:
                df, status = ncpor_live.fetch_live_weather(
                    station_id, timeout=config.NCPOR_LIVE_TIMEOUT_SECONDS
                )
                _save_cache(df, station_id)
                return df, status
            except Exception as exc:
                logger.warning("Live NCPOR fetch failed for %s: %s", station_id, exc)
                cached = _load_cache(station_id)
                if cached is not None:
                    return cached, {"found": True, "cached": True, "message": f"Live NCPOR unavailable; using last cached REAL_OBSERVED observation for {station_id}."}
                return None, {"found": False, "live_attempted": True, "message": f"NCPOR live fetch failed for {station_id}: {exc}"}
        logger.info("No local NCPOR export found for %s. Expected at %s/%s_aws.csv",
                    station_id, config.RAW_NCPOR_DIR, station_id.lower())
        return None, {
            "found": False,
            "message": f"No NCPOR local export found for {station_id}.",
        }

    try:
        raw = pd.read_csv(path)
    except Exception as exc:
        logger.error("Failed to read NCPOR file %s: %s", path, exc)
        return None, {"found": True, "message": f"Found file but could not parse it: {exc}"}

    df = _map_columns(raw)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        logger.warning("NCPOR file %s missing required columns: %s", path, missing)
        return None, {
            "found": True,
            "message": f"File found at {path} but missing required columns {missing}. "
                       f"Falling back to simulated data.",
        }

    df["station_id"] = station_id
    df["source"] = "NCPOR"
    df["data_status"] = config.REAL_OBSERVED

    keep = ["station_id", "timestamp", "temperature_c", "humidity_pct",
            "pressure_hpa", "wind_speed_kmh", "wind_dir_deg", "source", "data_status"]
    for col in keep:
        if col not in df.columns:
            df[col] = None
    df = df[keep]

    logger.info("Loaded %d REAL_OBSERVED rows for %s from %s", len(df), station_id, path)
    return df, {"found": True, "message": f"Loaded {len(df)} rows from {os.path.basename(path)}."}
