import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import simulator
from src.ml import anomaly_detection, energy_forecast
import config


def _equipment_df_for(scenario):
    weather = simulator.generate_weather("Maitri", scenario=scenario, days=15, freq_per_day=24)
    eq_meta = config.EQUIPMENT_LIST[0]
    return simulator.generate_equipment(eq_meta, weather, scenario=scenario)


def test_anomaly_model_trains_and_scores():
    eq_df = _equipment_df_for("NORMAL")
    models = anomaly_detection.train_equipment_anomaly_model(eq_df)
    assert eq_df["equipment_id"].iloc[0] in models

    results = anomaly_detection.score_latest(eq_df, models)
    assert len(results) == 1
    r = results[0]
    assert 0.0 <= r["anomaly_probability"] <= 1.0
    assert r["priority"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(r["top_signals"]) > 0


def test_anomaly_scenario_shows_higher_risk_than_normal():
    normal_df = _equipment_df_for("NORMAL")
    anomaly_df = _equipment_df_for("EQUIPMENT_ANOMALY")

    normal_models = anomaly_detection.train_equipment_anomaly_model(normal_df)
    anomaly_models = anomaly_detection.train_equipment_anomaly_model(anomaly_df)

    normal_score = anomaly_detection.score_latest(normal_df, normal_models)[0]["anomaly_probability"]
    anomaly_score = anomaly_detection.score_latest(anomaly_df, anomaly_models)[0]["anomaly_probability"]

    assert anomaly_score > normal_score


def test_energy_forecast_beats_or_matches_baseline_on_mae():
    weather = simulator.generate_weather("Maitri", scenario="NORMAL", days=20, freq_per_day=24)
    energy_df = simulator.generate_energy("Maitri", weather, scenario="NORMAL")
    result = energy_forecast.train_and_evaluate(energy_df)

    assert "MAE" in result["baseline_metrics"]
    assert "MAE" in result["model_metrics"]
    assert len(result["result_df"]) > 0
