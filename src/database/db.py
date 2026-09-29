"""
src/database/db.py
Connection handling + repository-style helper functions for the SQLite
database. Kept dependency-free (stdlib sqlite3 + pandas) for easy Windows use.
"""

import sqlite3
import pandas as pd
from contextlib import contextmanager

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.database.models import SCHEMA_STATEMENTS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@contextmanager
def get_connection():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    """Create all tables if they do not already exist. Idempotent."""
    with get_connection() as conn:
        cur = conn.cursor()
        for stmt in SCHEMA_STATEMENTS:
            cur.execute(stmt)
    logger.info("Database schema initialized at %s", config.DATABASE_PATH)


def seed_stations():
    with get_connection() as conn:
        cur = conn.cursor()
        for sid, meta in config.STATIONS.items():
            cur.execute(
                """INSERT OR IGNORE INTO stations
                   (station_id, full_name, latitude, longitude, region, established)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, meta["full_name"], meta["latitude"], meta["longitude"],
                 meta["region"], meta["established"]),
            )
        for eq in config.EQUIPMENT_LIST:
            cur.execute(
                """INSERT OR IGNORE INTO equipment (equipment_id, station_id, name, category)
                   VALUES (?, ?, ?, ?)""",
                (eq["id"], eq["station"], eq["name"], eq["category"]),
            )
    logger.info("Seeded stations and equipment master data.")


def bulk_insert_df(table, df):
    """Insert a DataFrame's rows into `table` using the DataFrame's own columns."""
    if df is None or df.empty:
        return 0
    with get_connection() as conn:
        df.to_sql(table, conn, if_exists="append", index=False)
    return len(df)


def read_table(table, where=None, params=None):
    with get_connection() as conn:
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        return pd.read_sql_query(query, conn, params=params)


def clear_table(table):
    with get_connection() as conn:
        conn.execute(f"DELETE FROM {table}")


def log_event(event, details=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (event, details) VALUES (?, ?)", (event, details)
        )


def record_data_source(dataset_name, source_org, station_id, dataset_type,
                        data_status, access_status, notes=""):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO data_sources
               (dataset_name, source_org, station_id, dataset_type, data_status,
                access_status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (dataset_name, source_org, station_id, dataset_type, data_status,
             access_status, notes),
        )


def sync_pipeline_snapshot(result):
    """Persist the current Digital Twin snapshot for audit and inspection.

    This is a snapshot store, not a replacement for an authorised station
    telemetry database. Operational tables are refreshed atomically so the
    bundled SQLite database reflects the same state shown by the dashboard.
    """
    with get_connection() as conn:
        tables = [
            "weather_readings", "equipment_readings", "energy_readings",
            "inventory", "logistics", "communication_status", "predictions",
            "alerts", "recommendations"
        ]
        for table in tables:
            conn.execute(f"DELETE FROM {table}")

        for sid, s in result.get("stations", {}).items():
            w = s.get("weather_df")
            if w is not None and not w.empty:
                cols = ["station_id", "timestamp", "temperature_c", "humidity_pct", "pressure_hpa",
                        "wind_speed_kmh", "wind_dir_deg", "source", "data_status"]
                w[cols].to_sql("weather_readings", conn, if_exists="append", index=False)

            e = s.get("equipment_df")
            if e is not None and not e.empty:
                cols = ["equipment_id", "timestamp", "temperature_c", "vibration_mm_s",
                        "operating_hours", "load_pct", "voltage_v", "source", "data_status"]
                e[cols].to_sql("equipment_readings", conn, if_exists="append", index=False)

            energy = s.get("energy_df")
            if energy is not None and not energy.empty:
                cols = ["station_id", "timestamp", "production_kw", "consumption_kw",
                        "fuel_level_pct", "generator_load_pct", "source", "data_status"]
                energy[cols].to_sql("energy_readings", conn, if_exists="append", index=False)

            inv = s.get("inventory_df")
            if inv is not None and not inv.empty:
                cols = ["station_id", "item_name", "category", "quantity", "min_stock",
                        "daily_usage", "lead_time_days", "criticality", "source", "data_status"]
                inv[cols].to_sql("inventory", conn, if_exists="append", index=False)

            logi = s.get("logistics_df")
            if logi is not None and not logi.empty:
                cols = ["station_id", "item", "mode", "expected_arrival", "cargo_priority",
                        "weather_dependency", "route_status", "source", "data_status"]
                logi[cols].to_sql("logistics", conn, if_exists="append", index=False)

            comm = s.get("communication")
            if comm:
                pd.DataFrame([comm])[['station_id', 'status', 'last_sync', 'pending_items', 'source', 'data_status']].to_sql(
                    "communication_status", conn, if_exists="append", index=False
                )

            preds = []
            for r in s.get("anomaly_results", []):
                preds.append({
                    "station_id": sid, "equipment_id": r.get("equipment_id"),
                    "model_name": "Equipment Anomaly Detection", "target": "anomaly_probability",
                    "prediction": r.get("anomaly_probability"), "confidence": None,
                    "explanation": "; ".join(f"{x['feature']} {x['direction']}" for x in r.get("top_signals", [])),
                    "timestamp": r.get("timestamp"), "data_status": config.MODEL_PREDICTION,
                })
            if preds:
                pd.DataFrame(preds).to_sql("predictions", conn, if_exists="append", index=False)

            alerts = s.get("alerts", [])
            if alerts:
                pd.DataFrame(alerts)[["station_id", "category", "severity", "timestamp",
                    "trigger_text", "explanation", "recommended_action", "status"]].to_sql(
                    "alerts", conn, if_exists="append", index=False)

            recs = s.get("recommendations", [])
            if recs:
                pd.DataFrame(recs)[["station_id", "priority", "title", "reason", "category", "timestamp"]].to_sql(
                    "recommendations", conn, if_exists="append", index=False)

        conn.execute(
            "INSERT INTO audit_logs (event, details) VALUES (?, ?)",
            ("PIPELINE_SNAPSHOT_SYNC", f"scenario={result.get('scenario')} data_mode={result.get('data_mode')}")
        )
