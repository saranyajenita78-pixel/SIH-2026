import pandas as pd

import config
from src.data import ncpor_live, ncpor_loader, imd_loader


def test_ncpor_live_parser_converts_knots_to_kmh():
    html = (
        "09 Sep 2026 11:59 PM Air Temperature: -20.20° C "
        "Relative Humidity: 23.68% Air Pressure: 964.58 mBar "
        "Wind Speed and Direction: 24.80 knots & 222° SW"
    )
    df = ncpor_live._parse_live_html("Maitri", html)
    html_tagged = "<span>09 Sep 2026 11:59 PM</span> <b>Air Temperature:</b> -20.20° C Relative Humidity: 23.68% Air Pressure: 964.58 mBar Wind Speed and Direction: 24.80 knots &amp; 222° SW"
    assert ncpor_live._parse_live_html("Maitri", html_tagged).iloc[0]["temperature_c"] == -20.2
    row = df.iloc[0]
    assert row["data_status"] == config.REAL_OBSERVED
    assert row["temperature_c"] == -20.2
    assert abs(row["wind_speed_kmh"] - 45.9296) < 1e-6
    assert row["wind_dir_deg"] == 222.0



def test_ncpor_bharati_live_format_without_colon_after_wind_speed():
    html = (
        "17 May 2026 Temperature: -15.20° C "
        "Relative Humidity: 61.52% Air Pressure: 990.17 mBar "
        "Wind Speed 10.90 knots"
    )
    df = ncpor_live._parse_live_html("Bharati", html)
    row = df.iloc[0]
    assert row["temperature_c"] == -15.2
    assert row["humidity_pct"] == 61.52
    assert row["pressure_hpa"] == 990.17
    assert abs(row["wind_speed_kmh"] - (10.90 * 1.852)) < 1e-6
    assert pd.isna(row["wind_dir_deg"])

def test_ncpor_local_csv_is_real_observed(tmp_path, monkeypatch):
    csv = tmp_path / "maitri_aws.csv"
    pd.DataFrame({
        "timestamp": ["2026-09-01 00:00"],
        "temperature": [-18.0],
        "humidity": [40],
        "pressure": [970],
        "wind_speed": [30],
        "wind_direction": [180],
    }).to_csv(csv, index=False)
    monkeypatch.setattr(config, "RAW_NCPOR_DIR", str(tmp_path))
    monkeypatch.setattr(config, "NCPOR_LIVE_ENABLED", False)
    df, status = ncpor_loader.load_station_weather("Maitri")
    assert status["found"] is True
    assert df.iloc[0]["data_status"] == config.REAL_OBSERVED


def test_imd_forecast_csv_is_real_forecast(tmp_path, monkeypatch):
    csv = tmp_path / "bharati_polar_wrf.csv"
    pd.DataFrame({
        "valid_time": ["2026-09-14 00:00", "2026-09-14 03:00"],
        "temperature": [-20, -21],
        "rh": [60, 62],
        "mslp": [980, 979],
        "wind_speed_knots": [10, 12],
    }).to_csv(csv, index=False)
    monkeypatch.setattr(config, "RAW_IMD_DIR", str(tmp_path))
    df, status = imd_loader.load_station_forecast("Bharati")
    assert status["found"] is True
    assert len(df) == 2
    assert set(df["data_status"]) == {config.REAL_FORECAST}
    assert abs(df.iloc[0]["wind_speed_kmh"] - 18.52) < 1e-6


def test_real_pipeline_keeps_operational_modules_populated_with_latest_only_weather(monkeypatch):
    from src.pipeline import run_full_pipeline
    def fake_load(station_id):
        return pd.DataFrame([{
            "station_id": station_id, "timestamp": "2026-09-14 00:00",
            "temperature_c": -18.0, "humidity_pct": 50.0, "pressure_hpa": 970.0,
            "wind_speed_kmh": 25.0, "wind_dir_deg": 180.0,
            "source": "NCPOR/NPDC Live", "data_status": config.REAL_OBSERVED
        }]), {"found": True, "message": "test REAL observation"}
    monkeypatch.setattr(ncpor_loader, "load_station_weather", fake_load)
    result = run_full_pipeline("NORMAL", data_mode="REAL")
    for station in result["stations"].values():
        assert not station["equipment_df"].empty
        assert not station["energy_df"].empty


def test_historical_snowfall_export_returns_maximum(tmp_path, monkeypatch):
    from src.data import historical
    csv = tmp_path / "maitri_historical.csv"
    pd.DataFrame({
        "timestamp": ["2020-01-01", "2020-01-02", "2020-01-03"],
        "snowfall": [2.0, 8.5, 4.0],
    }).to_csv(csv, index=False)
    monkeypatch.setattr(historical, "HISTORICAL_DIR", str(tmp_path))
    result = historical.maximum_snowfall("Maitri")
    assert len(result) == 1
    assert result.iloc[0]["snowfall_mm"] == 8.5
