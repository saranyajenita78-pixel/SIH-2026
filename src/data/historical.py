"""Optional historical Antarctic weather/snow data loader.

The public NCPOR portal lists historical datasets, but the portal does not
expose a stable documented machine-readable snowfall API. This adapter accepts
an authorised NCPOR/IMD export placed in data/raw/ncpor/historical/ and keeps
its provenance explicit. It never creates historical snowfall values.
"""
import json
import os
import pandas as pd
import config

HISTORICAL_DIR = os.path.join(config.RAW_NCPOR_DIR, "historical")
os.makedirs(HISTORICAL_DIR, exist_ok=True)

ALIASES = {
    "timestamp": ["timestamp", "date", "datetime", "valid_time", "date_time", "time"],
    "station_id": ["station_id", "station", "station_name", "location"],
    "snowfall_mm": ["snowfall_mm", "snowfall", "snow_mm", "snow", "snow_accumulation_mm", "snowfall_amount"],
    "snow_depth_m": ["snow_depth_m", "snow_depth", "snowdepth", "snow_depth_meter", "snow_depth_metres"],
    "precipitation_mm": ["precipitation_mm", "precipitation", "precip_mm", "rain_snow_mm", "precip_total"],
}


def _map_columns(df):
    lower = {str(c).strip().lower(): c for c in df.columns}
    rename = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lower:
                rename[lower[alias]] = target
                break
    return df.rename(columns=rename)


def _files_for_station(station_id):
    if not os.path.isdir(HISTORICAL_DIR):
        return []
    return [os.path.join(HISTORICAL_DIR, f) for f in os.listdir(HISTORICAL_DIR)
            if station_id.lower() in f.lower() and f.lower().endswith((".csv", ".json"))]


def load_station_history(station_id):
    """Return official-export history or an empty frame; never synthesize values."""
    frames = []
    for path in _files_for_station(station_id):
        try:
            if path.lower().endswith(".json"):
                with open(path, "r", encoding="utf-8") as fh:
                    obj = json.load(fh)
                raw = pd.DataFrame(obj if isinstance(obj, list) else obj.get("data", []))
            else:
                raw = pd.read_csv(path)
            df = _map_columns(raw)
            if "timestamp" not in df.columns:
                continue
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"]).copy()
            for col in ["snowfall_mm", "snow_depth_m", "precipitation_mm"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df["station_id"] = station_id
            df["source"] = "Official historical export supplied to Polar Twin Sentinel"
            df["data_status"] = config.REAL_OBSERVED
            frames.append(df)
        except Exception:
            continue
    if not frames:
        return pd.DataFrame(), {"found": False, "message": "No official historical export loaded."}
    out = pd.concat(frames, ignore_index=True).sort_values("timestamp").drop_duplicates()
    return out, {"found": True, "message": f"Loaded {len(out)} historical rows from official export(s)."}


def maximum_snowfall(station_id=None):
    stations = [station_id] if station_id else list(config.STATIONS)
    rows = []
    for sid in stations:
        df, _ = load_station_history(sid)
        if df.empty or "snowfall_mm" not in df.columns:
            continue
        valid = df.dropna(subset=["snowfall_mm"])
        if valid.empty:
            continue
        row = valid.loc[valid["snowfall_mm"].idxmax()]
        rows.append({"station_id": sid, "timestamp": row["timestamp"],
                     "snowfall_mm": float(row["snowfall_mm"]), "source": row["source"]})
    if not rows:
        return pd.DataFrame(columns=["station_id", "timestamp", "snowfall_mm", "source"])
    return pd.DataFrame(rows).sort_values("snowfall_mm", ascending=False).reset_index(drop=True)
