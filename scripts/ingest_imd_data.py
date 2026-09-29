"""Check official IMD Polar WRF forecast exports supplied to the project."""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.data import imd_loader
for station in config.STATIONS:
    df, status = imd_loader.load_station_forecast(station)
    print(f"[{station}] {'REAL_FORECAST' if df is not None else 'NOT LOADED'} — {status['message']}")
