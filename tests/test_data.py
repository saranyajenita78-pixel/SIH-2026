import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import simulator, data_validator, preprocessing


def test_generate_weather_shape_and_status():
    df = simulator.generate_weather("Maitri", scenario="NORMAL", days=5, freq_per_day=24)
    assert len(df) == 5 * 24
    assert (df["data_status"] == "SIMULATED_DEMO").all()
    assert (df["source"] == "DEMO_SIMULATOR").all()
    assert df["temperature_c"].between(-90, 20).all()


def test_extreme_weather_scenario_colder_and_windier_than_normal():
    normal = simulator.generate_weather("Maitri", scenario="NORMAL", days=10, freq_per_day=24)
    extreme = simulator.generate_weather("Maitri", scenario="EXTREME_WEATHER", days=10, freq_per_day=24)
    # Compare the final quarter, where the scenario ramp is fully applied.
    n_tail = normal.iloc[-60:]
    e_tail = extreme.iloc[-60:]
    assert e_tail["wind_speed_kmh"].mean() > n_tail["wind_speed_kmh"].mean()
    assert e_tail["temperature_c"].mean() < n_tail["temperature_c"].mean()


def test_validate_dataframe_flags_missing_columns():
    df = pd.DataFrame({"timestamp": ["2024-01-01T00:00:00"]})
    is_valid, issues = data_validator.validate_dataframe(df, ["timestamp", "temperature_c"])
    assert not is_valid
    assert any("Missing required columns" in i for i in issues)


def test_validate_dataframe_flags_out_of_range():
    df = pd.DataFrame({
        "timestamp": ["2024-01-01T00:00:00"],
        "temperature_c": [500.0],
    })
    is_valid, issues = data_validator.validate_dataframe(df, ["timestamp", "temperature_c"])
    assert any("out-of-range" in i for i in issues)


def test_clean_weather_sorts_and_dedupes():
    df = pd.DataFrame({
        "station_id": ["Maitri", "Maitri", "Maitri"],
        "timestamp": ["2024-01-01T02:00:00", "2024-01-01T00:00:00", "2024-01-01T00:00:00"],
        "temperature_c": [-10.0, -12.0, -12.0],
        "humidity_pct": [50, 55, 55],
        "pressure_hpa": [980, 981, 981],
        "wind_speed_kmh": [10, 12, 12],
        "wind_dir_deg": [100, 110, 110],
    })
    cleaned = preprocessing.clean_weather(df)
    assert len(cleaned) == 2  # duplicate row removed
    assert cleaned.iloc[0]["timestamp"] < cleaned.iloc[1]["timestamp"]


def test_simulator_seed_is_stable_for_same_station_and_scenario():
    from src.data import simulator
    a = simulator.generate_weather("Maitri", "NORMAL", days=1)
    b = simulator.generate_weather("Maitri", "NORMAL", days=1)
    assert a[["temperature_c", "wind_speed_kmh", "pressure_hpa"]].equals(
        b[["temperature_c", "wind_speed_kmh", "pressure_hpa"]]
    )
