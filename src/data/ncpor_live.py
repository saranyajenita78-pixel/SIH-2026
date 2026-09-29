"""Live NCPOR/NPDC weather adapter.

The NPDC public station pages expose the latest station observation as HTML.
This module parses only those published values; it does not invent missing
measurements.  Historical data should still be supplied as an official CSV
export through ``ncpor_loader`` when model training needs a longer series.
"""

import html
import re
from datetime import datetime

import pandas as pd

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

import config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

LIVE_URLS = {
    "Maitri": "https://data.ncpor.res.in/live/maitri",
    "Bharati": "https://data.ncpor.res.in/bharati/live",
}


def _clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _first(pattern, text, flags=re.I):
    match = re.search(pattern, text, flags)
    return _clean_text(match.group(1)) if match else None


def _parse_live_html(station_id, text):
    # Keep the parser tolerant of whitespace/nbsp differences in the portal.
    text = _clean_text(text)
    date_text = _first(
        r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM))?)\s+Air Temperature",
        text,
    ) or _first(
        r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM))?)\s+Temperature",
        text,
    )

    temp = _first(r"(?:Air )?Temperature:\s*(-?\d+(?:\.\d+)?)\s*°?\s*C", text)
    humidity = _first(r"(?:Relative )?Humidity:\s*(\d+(?:\.\d+)?)\s*%", text)
    pressure = _first(r"Air Pressure:\s*(\d+(?:\.\d+)?)\s*mBar", text)
    wind_knots = _first(r"Wind Speed(?: and Direction)?\s*:?\s*(\d+(?:\.\d+)?)\s*knots", text)
    wind_dir = _first(r"Wind Speed and Direction\s*:?\s*\d+(?:\.\d+)?\s*knots\s*&\s*(\d+(?:\.\d+)?)", text)

    if temp is None or pressure is None or wind_knots is None:
        raise ValueError("Could not parse the required NCPOR live weather fields")

    timestamp = pd.to_datetime(date_text, errors="coerce") if date_text else pd.Timestamp.utcnow()
    if pd.isna(timestamp):
        timestamp = pd.Timestamp.utcnow()

    return pd.DataFrame([{
        "station_id": station_id,
        "timestamp": timestamp,
        "temperature_c": float(temp),
        "humidity_pct": float(humidity) if humidity is not None else None,
        "pressure_hpa": float(pressure),
        "wind_speed_kmh": float(wind_knots) * 1.852,
        "wind_dir_deg": float(wind_dir) if wind_dir is not None else None,
        "source": "NCPOR/NPDC Live",
        "data_status": config.REAL_OBSERVED,
    }])


def fetch_live_weather(station_id, timeout=15):
    """Fetch one latest published observation from the public NPDC page."""
    if requests is None:
        raise RuntimeError("requests is required for live NCPOR ingestion")
    url = LIVE_URLS.get(station_id)
    if not url:
        raise ValueError(f"Unsupported NCPOR station: {station_id}")
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "PolarOps-AI/1.0"})
    response.raise_for_status()
    df = _parse_live_html(station_id, response.text)
    logger.info("Fetched %d live REAL_OBSERVED row(s) for %s from NCPOR", len(df), station_id)
    return df, {"found": True, "url": url, "message": f"Latest observation fetched from NCPOR/NPDC ({url})."}
