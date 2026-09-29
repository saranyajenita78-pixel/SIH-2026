"""
src/database/models.py
Raw-SQL schema definitions for the Antarctic Station Intelligence Platform.

SQLite is used (see config.DATABASE_PATH) via the stdlib sqlite3 module so the
project has zero heavyweight DB dependency and runs anywhere Python runs.
"""

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS stations (
        station_id      TEXT PRIMARY KEY,
        full_name       TEXT NOT NULL,
        latitude        REAL,
        longitude       REAL,
        region          TEXT,
        established     INTEGER,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS weather_readings (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id      TEXT NOT NULL,
        timestamp       TEXT NOT NULL,
        temperature_c   REAL,
        humidity_pct    REAL,
        pressure_hpa    REAL,
        wind_speed_kmh  REAL,
        wind_dir_deg    REAL,
        source          TEXT NOT NULL,
        data_status     TEXT NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS equipment (
        equipment_id    TEXT PRIMARY KEY,
        station_id      TEXT NOT NULL,
        name            TEXT NOT NULL,
        category        TEXT NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS equipment_readings (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id        TEXT NOT NULL,
        timestamp           TEXT NOT NULL,
        temperature_c       REAL,
        vibration_mm_s      REAL,
        operating_hours     REAL,
        load_pct            REAL,
        voltage_v           REAL,
        source              TEXT NOT NULL,
        data_status         TEXT NOT NULL,
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS energy_readings (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id          TEXT NOT NULL,
        timestamp           TEXT NOT NULL,
        production_kw       REAL,
        consumption_kw      REAL,
        fuel_level_pct      REAL,
        generator_load_pct  REAL,
        source              TEXT NOT NULL,
        data_status         TEXT NOT NULL,
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id          TEXT NOT NULL,
        item_name           TEXT NOT NULL,
        category            TEXT NOT NULL,
        quantity            REAL NOT NULL,
        min_stock           REAL NOT NULL,
        daily_usage         REAL NOT NULL,
        lead_time_days      REAL NOT NULL,
        criticality         TEXT NOT NULL,
        source              TEXT NOT NULL,
        data_status         TEXT NOT NULL,
        updated_at          TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS logistics (
        logistics_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id          TEXT NOT NULL,
        item                TEXT,
        mode                TEXT,
        expected_arrival    TEXT,
        cargo_priority      TEXT,
        weather_dependency  TEXT,
        route_status        TEXT,
        source              TEXT NOT NULL,
        data_status         TEXT NOT NULL,
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS communication_status (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id      TEXT NOT NULL,
        status          TEXT NOT NULL,
        last_sync       TEXT,
        pending_items   INTEGER DEFAULT 0,
        source          TEXT NOT NULL,
        data_status     TEXT NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS predictions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id      TEXT,
        equipment_id    TEXT,
        model_name      TEXT NOT NULL,
        target          TEXT NOT NULL,
        prediction      REAL,
        confidence      REAL,
        explanation     TEXT,
        timestamp       TEXT NOT NULL,
        data_status     TEXT NOT NULL DEFAULT 'MODEL_PREDICTION',
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id      TEXT NOT NULL,
        category        TEXT NOT NULL,
        severity        TEXT NOT NULL,
        timestamp       TEXT NOT NULL,
        trigger_text    TEXT NOT NULL,
        explanation     TEXT,
        recommended_action TEXT,
        status          TEXT DEFAULT 'OPEN',
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS recommendations (
        rec_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id      TEXT NOT NULL,
        priority        INTEGER NOT NULL,
        title           TEXT NOT NULL,
        reason          TEXT,
        category        TEXT,
        timestamp       TEXT NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS data_sources (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_name    TEXT NOT NULL,
        source_org      TEXT NOT NULL,
        station_id      TEXT,
        dataset_type    TEXT NOT NULL,
        data_status     TEXT NOT NULL,
        access_status   TEXT,
        notes           TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS model_runs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name      TEXT NOT NULL,
        trained_at      TEXT NOT NULL,
        metrics_json    TEXT,
        notes           TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event           TEXT NOT NULL,
        details         TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
]
