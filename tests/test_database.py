import os
import sys
import tempfile
import importlib

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def temp_db(monkeypatch, tmp_path):
    """Points config.DATABASE_PATH at a throwaway temp file for this test."""
    import config
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "DATABASE_PATH", str(db_path))
    from src.database import db as db_module
    importlib.reload(db_module)
    return db_module


def test_initialize_database_creates_tables(temp_db):
    temp_db.initialize_database()
    stations_df = temp_db.read_table("stations")
    assert list(stations_df.columns).count("station_id") == 1 or "station_id" in stations_df.columns


def test_seed_stations_inserts_expected_rows(temp_db):
    temp_db.initialize_database()
    temp_db.seed_stations()
    stations_df = temp_db.read_table("stations")
    assert set(stations_df["station_id"]) == {"Maitri", "Bharati"}

    equipment_df = temp_db.read_table("equipment")
    assert len(equipment_df) == 8


def test_seed_is_idempotent(temp_db):
    temp_db.initialize_database()
    temp_db.seed_stations()
    temp_db.seed_stations()  # run twice, should not duplicate or error
    stations_df = temp_db.read_table("stations")
    assert len(stations_df) == 2
