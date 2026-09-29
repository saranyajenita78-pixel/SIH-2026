"""
scripts/ingest_ncpor_data.py
Standalone CLI wrapper around src/data/ncpor_loader.py — checks every station
for a locally-supplied NCPOR export and reports status. Does not touch the
database (that happens as part of the live pipeline / generate_demo_data.py);
this script is a quick way to confirm whether real data has been detected.

Run:  python scripts/ingest_ncpor_data.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.data import ncpor_loader
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 60)
    print(" NCPOR / NPDC ingestion check")
    print("=" * 60)
    for station_id in config.STATIONS:
        df, status = ncpor_loader.load_station_weather(station_id)
        if df is not None:
            print(f"[{station_id}] REAL_OBSERVED  — {status['message']}")
        else:
            print(f"[{station_id}] NOT LOADED — {status['message']}")
    print("=" * 60)
    print("Local historical export path (optional):")
    for station_id in config.STATIONS:
        print(f"  data/raw/ncpor/{station_id.lower()}_aws.csv")


if __name__ == "__main__":
    main()
