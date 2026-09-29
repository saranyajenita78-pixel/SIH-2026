import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.risk import risk_engine


def test_weather_risk_low_for_mild_conditions():
    row = pd.Series({"temperature_c": -10.0, "wind_speed_kmh": 15.0})
    result = risk_engine.weather_risk(row, pressure_change_6h=0.5)
    assert result["level"] in ("LOW", "MEDIUM")
    assert result["score"] < 50


def test_weather_risk_high_for_extreme_conditions():
    row = pd.Series({"temperature_c": -40.0, "wind_speed_kmh": 110.0})
    result = risk_engine.weather_risk(row, pressure_change_6h=10.0)
    assert result["level"] in ("HIGH", "CRITICAL")
    assert result["score"] >= 50


def test_inventory_risk_flags_low_buffer_item():
    df = pd.DataFrame([
        {"station_id": "Maitri", "item_name": "Critical Spare", "quantity": 5,
         "daily_usage": 1.0, "lead_time_days": 90, "criticality": "Very High"},
        {"station_id": "Maitri", "item_name": "Consumable", "quantity": 500,
         "daily_usage": 1.0, "lead_time_days": 10, "criticality": "Low"},
    ])
    result = risk_engine.inventory_risk(df)
    assert result["score"] > 0
    assert "Critical Spare" in result["explanation"]


def test_overall_risk_weighted_sum():
    sub_risks = {
        "weather": {"score": 100.0},
        "equipment": {"score": 0.0},
        "energy": {"score": 0.0},
        "inventory": {"score": 0.0},
        "logistics": {"score": 0.0},
        "communication": {"score": 0.0},
    }
    result = risk_engine.overall_risk(sub_risks)
    import config
    expected = 100.0 * config.RISK_WEIGHTS["weather"]
    assert abs(result["score"] - expected) < 0.01


def test_weather_temperature_risk_decreases_as_temperature_warms_within_cold_range():
    import pandas as pd
    scores = []
    for t in (-40.0, -30.0, -20.0, -10.0):
        row = pd.Series({"temperature_c": t, "wind_speed_kmh": 0.0})
        scores.append(risk_engine.weather_risk(row, 0.0)["factors"])
    vals = [next(x["contribution"] for x in fs if x["factor"] == "Temperature") for fs in scores]
    assert vals == sorted(vals, reverse=True)
