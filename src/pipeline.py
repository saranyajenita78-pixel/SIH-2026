"""
src/pipeline.py
Orchestrates the full OBSERVE -> ANALYZE -> PREDICT -> PRIORITIZE -> ALERT ->
RECOMMEND -> DECIDE chain for a given scenario. This is the single function
the Streamlit dashboard calls (and it is what scripts/train_models.py and the
test suite exercise too), so behaviour stays identical everywhere.
"""

from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

import config
from src.data import simulator, ncpor_loader, imd_loader, historical, data_validator, preprocessing
from src.ml import anomaly_detection, energy_forecast
from src.risk import risk_engine
from src.alerts import alert_engine
from src.recommendations import recommendation_engine
from src.database import db
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_weather_for_station(station_id, scenario, data_mode=None):
    """Load NCPOR observations. REAL mode never silently substitutes demo weather."""
    data_mode = (data_mode or config.DATA_MODE).upper()
    # DEMO mode is intentionally offline-fast; it does not wait for network
    # calls because every DEMO weather value is explicitly synthetic.
    if data_mode == "DEMO":
        sim_df = simulator.generate_weather(station_id, scenario=scenario)
        return sim_df, "SIMULATED_DEMO weather generated for hackathon demo mode."

    real_df, status = ncpor_loader.load_station_weather(station_id)
    if real_df is not None and not real_df.empty:
        is_valid, issues = data_validator.validate_dataframe(
            real_df, ["station_id", "timestamp", "temperature_c"])
        if is_valid:
            cleaned = preprocessing.clean_weather(real_df)
            return cleaned, status["message"]
        logger.warning("NCPOR data for %s failed validation: %s", station_id, issues)
        status = {"message": f"NCPOR data failed validation for {station_id}: {issues}"}

    # REAL mode is strict: never manufacture a weather reading. The dashboard
    # may use a previously cached REAL_OBSERVED row, but if neither a fresh
    # public observation nor a real local export/cache exists, stop the weather
    # pipeline rather than displaying synthetic values as current weather.
    raise RuntimeError(
        f"No verified REAL_OBSERVED NCPOR weather is available for {station_id}. "
        f"The public NCPOR source could not be reached and no real cache/export exists. "
        f"No synthetic weather is substituted in REAL mode. Details: {status.get('message', '')}"
    )


def run_full_pipeline(scenario="NORMAL", data_mode=None):
    """
    Runs the complete pipeline for BOTH stations under the given Demo Mode
    scenario and returns one consolidated dict the dashboard can render
    directly, with no further business logic needed in the UI layer.
    """
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data_mode = (data_mode or config.DATA_MODE).upper()
    output = {"generated_at": now_iso, "scenario": scenario, "data_mode": data_mode, "stations": {}}

    # Fetch the two independent public NCPOR station pages concurrently.
    # This prevents a slow/unreachable station from making the other station
    # wait for its network timeout. DEMO mode remains fully offline.
    station_ids = list(config.STATIONS.keys())
    weather_results = {}
    if data_mode == "DEMO":
        for station_id in station_ids:
            weather_results[station_id] = get_weather_for_station(station_id, scenario, data_mode=data_mode)
    else:
        with ThreadPoolExecutor(max_workers=len(station_ids)) as pool:
            futures = {pool.submit(get_weather_for_station, sid, scenario, data_mode): sid for sid in station_ids}
            for future in as_completed(futures):
                sid = futures[future]
                weather_results[sid] = future.result()

    for station_id in station_ids:
        weather_df, weather_provenance = weather_results[station_id]
        weather_df = weather_df.reset_index(drop=True)
        imd_forecast_df, imd_status = imd_loader.load_station_forecast(station_id)
        historical_df, historical_status = historical.load_station_history(station_id)
        snowfall_max = historical.maximum_snowfall(station_id)

        # NCPOR public live pages can expose one latest observation. Keep that
        # real stream intact, while generating a separate synthetic operational
        # history for equipment/energy models that require many samples.
        operational_weather_df = weather_df if len(weather_df) >= 24 else simulator.generate_weather(station_id, scenario=scenario)
        station_equipment = [e for e in config.EQUIPMENT_LIST if e["station"] == station_id]
        equipment_frames = [simulator.generate_equipment(eq, operational_weather_df, scenario=scenario)
                             for eq in station_equipment]
        equipment_df = pd.concat(equipment_frames, ignore_index=True) if equipment_frames else pd.DataFrame()

        energy_df = simulator.generate_energy(station_id, operational_weather_df, scenario=scenario)
        inventory_df_all = simulator.generate_inventory(scenario=scenario)
        inventory_df = inventory_df_all[inventory_df_all["station_id"] == station_id]
        logistics_df = simulator.generate_logistics(station_id, scenario=scenario)
        comm_df = simulator.generate_communication_status(station_id, scenario=scenario)

        # ---- ML ----
        # Use the saved normal-operation anomaly baseline when available.
        # Scenario telemetry is then scored against that baseline instead of
        # retraining on the anomaly itself, which is the correct predictive-
        # maintenance pattern and also reduces dashboard latency.
        anomaly_models = anomaly_detection.load_saved_model(station_id)
        if not anomaly_models:
            anomaly_models = anomaly_detection.train_equipment_anomaly_model(equipment_df)
        anomaly_results = anomaly_detection.score_latest(equipment_df, anomaly_models)

        # Fast path: inference from the saved offline-trained artifact.
        # Retraining is intentionally reserved for scripts/train_models.py and
        # the explicit model-building workflow, not every dashboard refresh.
        forecast_result = None
        try:
            forecast_result = energy_forecast.fast_forecast(energy_df, station_id)
        except Exception as exc:
            logger.warning("Energy forecast failed for %s: %s", station_id, exc)

        # ---- Risk ----
        latest_weather = weather_df.iloc[-1]
        pressure_change = float(weather_df["pressure_hpa"].iloc[-1] - weather_df["pressure_hpa"].iloc[-7]) \
            if len(weather_df) > 7 else 0.0

        sub_risks = {
            "weather": risk_engine.weather_risk(latest_weather, pressure_change),
            "equipment": risk_engine.equipment_risk(anomaly_results),
            "energy": risk_engine.energy_risk(energy_df.iloc[-1]),
            "inventory": risk_engine.inventory_risk(inventory_df),
            "logistics": risk_engine.logistics_risk(logistics_df),
            "communication": risk_engine.communication_risk(comm_df.iloc[-1]),
        }
        overall = risk_engine.overall_risk(sub_risks)

        # ---- Alerts + Recommendations ----
        alerts = alert_engine.generate_alerts(station_id, sub_risks, timestamp=now_iso)
        recommendations = recommendation_engine.generate_recommendations(
            station_id, alerts, overall, timestamp=now_iso)
        decision_card = recommendation_engine.build_decision_card(
            station_id, overall, alerts, recommendations)

        output["stations"][station_id] = {
            "weather_df": weather_df,
            "weather_provenance": weather_provenance,
            "imd_forecast_df": imd_forecast_df if imd_forecast_df is not None else pd.DataFrame(),
            "imd_provenance": imd_status["message"],
            "historical_df": historical_df,
            "historical_provenance": historical_status["message"],
            "maximum_snowfall": snowfall_max,
            "equipment_df": equipment_df,
            "anomaly_results": anomaly_results,
            "energy_df": energy_df,
            "forecast_result": forecast_result,
            "inventory_df": inventory_df,
            "logistics_df": logistics_df,
            "communication": comm_df.iloc[0].to_dict(),
            "sub_risks": sub_risks,
            "overall_risk": overall,
            "alerts": alerts,
            "recommendations": recommendations,
            "decision_card": decision_card,
        }

    try:
        db.initialize_database()
        db.seed_stations()
        db.sync_pipeline_snapshot(output)
    except Exception as exc:
        logger.warning("Could not sync pipeline snapshot to SQLite: %s", exc)
    return output
