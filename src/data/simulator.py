"""
src/data/simulator.py
Deterministic, relationship-based simulator for operational telemetry that is
not otherwise available from a public NCPOR export. This is NOT random noise:
each domain is driven off the weather state so that cause -> effect chains
are visible and the hackathon Demo Mode is fully reproducible.

Chain implemented (see ARCHITECTURE.md):
    extreme weather -> higher heating/energy demand -> higher generator load
    -> higher equipment temperature/vibration -> higher anomaly probability
    -> higher consumption -> faster inventory depletion -> shortage risk

Every row produced here is tagged data_status = SIMULATED_DEMO and
source = 'DEMO_SIMULATOR' per the project's Data Integrity Policy.
"""

import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

SOURCE = "DEMO_SIMULATOR"


def _rng_for(station_id, scenario):
    """A dedicated RNG per (station, scenario) keeps the demo reproducible."""
    key = f"{station_id}|{scenario}".encode("utf-8")
    stable_hash = int(hashlib.sha256(key).hexdigest()[:8], 16)
    seed = config.SIM_RANDOM_SEED + stable_hash % 10_000
    return np.random.default_rng(seed)


def _scenario_multiplier(scenario, hour_index, total_hours):
    """
    Returns a dict of multipliers/offsets applied on top of the seasonal
    baseline, depending on which Demo Mode scenario is active.
    The anomaly is ramped in over the final third of the series so charts
    show a believable *trend*, not a step function.
    """
    ramp = np.clip((hour_index - total_hours * 0.6) / (total_hours * 0.4), 0, 1)

    if scenario == "NORMAL":
        return dict(wind_boost=0.0, temp_drop=0.0, vib_boost=0.0, temp_boost=0.0,
                    consumption_boost=0.0)
    if scenario == "EXTREME_WEATHER":
        return dict(wind_boost=55 * ramp, temp_drop=14 * ramp, vib_boost=0.0,
                    temp_boost=0.0, consumption_boost=0.15 * ramp)
    if scenario == "EQUIPMENT_ANOMALY":
        return dict(wind_boost=5 * ramp, temp_drop=1 * ramp, vib_boost=3.2 * ramp,
                    temp_boost=18 * ramp, consumption_boost=0.05 * ramp)
    if scenario == "RESOURCE_PRESSURE":
        return dict(wind_boost=5 * ramp, temp_drop=1 * ramp, vib_boost=0.0,
                    temp_boost=0.0, consumption_boost=0.35 * ramp)
    if scenario == "COMPOUND_EMERGENCY":
        return dict(wind_boost=55 * ramp, temp_drop=14 * ramp, vib_boost=3.2 * ramp,
                    temp_boost=18 * ramp, consumption_boost=0.40 * ramp)
    return dict(wind_boost=0.0, temp_drop=0.0, vib_boost=0.0, temp_boost=0.0,
                consumption_boost=0.0)


def generate_weather(station_id, scenario="NORMAL", days=None, freq_per_day=None):
    days = days or config.HISTORY_DAYS
    freq_per_day = freq_per_day or config.READINGS_PER_DAY
    n = days * freq_per_day
    rng = _rng_for(station_id, scenario)

    now = datetime.now(timezone.utc)
    timestamps = [now - timedelta(hours=(n - i)) for i in range(n)]

    hour_of_day = np.array([t.hour for t in timestamps])
    diurnal = -3 * np.cos(2 * np.pi * hour_of_day / 24)  # coldest at night

    base_temp = -18.0 if station_id == "Maitri" else -12.0
    base_wind = 25.0 if station_id == "Maitri" else 30.0
    base_pressure = 985.0

    rows = []
    for i, t in enumerate(timestamps):
        mult = _scenario_multiplier(scenario, i, n)
        temp = (base_temp + diurnal[i] - mult["temp_drop"]
                + rng.normal(0, 1.2))
        wind = max(0.0, base_wind + mult["wind_boost"] + rng.normal(0, 4.0))
        pressure = base_pressure - 0.4 * mult["wind_boost"] + rng.normal(0, 1.5)
        humidity = np.clip(60 + rng.normal(0, 8) - 0.1 * mult["wind_boost"], 15, 100)
        wind_dir = (rng.uniform(0, 360))

        rows.append({
            "station_id": station_id,
            "timestamp": t.isoformat(timespec="seconds"),
            "temperature_c": round(float(temp), 2),
            "humidity_pct": round(float(humidity), 1),
            "pressure_hpa": round(float(pressure), 1),
            "wind_speed_kmh": round(float(wind), 1),
            "wind_dir_deg": round(float(wind_dir), 1),
            "source": SOURCE,
            "data_status": config.SIMULATED_DEMO,
        })
    return pd.DataFrame(rows)


def generate_equipment(equipment_row, weather_df, scenario="NORMAL"):
    """Equipment telemetry driven off the same weather series (shared index)."""
    station_id = equipment_row["station"]
    eq_id = equipment_row["id"]
    rng = _rng_for(eq_id, scenario)
    n = len(weather_df)

    base_vibration = 1.8 if equipment_row["category"] == "Power" else 0.8
    base_temp = 55.0 if equipment_row["category"] == "Power" else 35.0
    base_load = 60.0 if equipment_row["category"] == "Power" else 40.0

    rows = []
    op_hours = rng.uniform(4000, 9000)
    for i in range(n):
        mult = _scenario_multiplier(scenario, i, n)
        cold_penalty = max(0.0, -weather_df.iloc[i]["temperature_c"] - 15) * 0.4
        load = np.clip(base_load + cold_penalty + mult["consumption_boost"] * 100
                        + rng.normal(0, 3), 10, 100)
        vibration = max(0.0, base_vibration + mult["vib_boost"] + rng.normal(0, 0.15)
                         + (load - base_load) * 0.01)
        temperature = base_temp + mult["temp_boost"] + (load - base_load) * 0.3 + rng.normal(0, 1.5)
        voltage = np.clip(230 + rng.normal(0, 3) - 0.05 * mult["vib_boost"], 190, 250)
        op_hours += rng.uniform(0.9, 1.0)

        rows.append({
            "equipment_id": eq_id,
            "timestamp": weather_df.iloc[i]["timestamp"],
            "temperature_c": round(float(temperature), 2),
            "vibration_mm_s": round(float(vibration), 3),
            "operating_hours": round(float(op_hours), 1),
            "load_pct": round(float(load), 1),
            "voltage_v": round(float(voltage), 1),
            "source": SOURCE,
            "data_status": config.SIMULATED_DEMO,
        })
    return pd.DataFrame(rows)


def generate_energy(station_id, weather_df, scenario="NORMAL"):
    rng = _rng_for(station_id + "_energy", scenario)
    n = len(weather_df)
    base_prod = 180.0
    fuel = 90.0  # starting fuel level percentage

    rows = []
    for i in range(n):
        mult = _scenario_multiplier(scenario, i, n)
        cold_penalty = max(0.0, -weather_df.iloc[i]["temperature_c"] - 15) * 1.8
        consumption = np.clip(140 + cold_penalty + mult["consumption_boost"] * 120
                               + rng.normal(0, 5), 60, 260)
        production = base_prod + rng.normal(0, 4)
        gen_load = np.clip((consumption / max(production, 1)) * 70, 20, 100)
        fuel = max(0.0, fuel - (consumption / 5000.0))

        rows.append({
            "station_id": station_id,
            "timestamp": weather_df.iloc[i]["timestamp"],
            "production_kw": round(float(production), 1),
            "consumption_kw": round(float(consumption), 1),
            "fuel_level_pct": round(float(fuel), 2),
            "generator_load_pct": round(float(gen_load), 1),
            "source": SOURCE,
            "data_status": config.SIMULATED_DEMO,
        })
    return pd.DataFrame(rows)


def generate_inventory(scenario="NORMAL"):
    """Applies a consumption multiplier to the static base inventory config."""
    mult = _scenario_multiplier(scenario, 100, 100)  # fully ramped-in value
    usage_multiplier = 1.0 + mult["consumption_boost"]

    rows = []
    for item in config.INVENTORY_ITEMS:
        daily_usage = round(item["daily_usage"] * usage_multiplier, 3)
        rows.append({
            "station_id": item["station"],
            "item_name": item["item"],
            "category": item["category"],
            "quantity": item["stock"],
            "min_stock": item["min_stock"],
            "daily_usage": daily_usage,
            "lead_time_days": item["lead_time_days"],
            "criticality": item["criticality"],
            "source": SOURCE,
            "data_status": config.SIMULATED_DEMO,
        })
    return pd.DataFrame(rows)


def generate_logistics(station_id, scenario="NORMAL"):
    rng = _rng_for(station_id + "_logistics", scenario)
    now = datetime.now(timezone.utc)
    weather_dependency = "High" if scenario in ("EXTREME_WEATHER", "COMPOUND_EMERGENCY") else "Medium"
    route_status = "Delayed - weather window closed" if scenario in (
        "EXTREME_WEATHER", "COMPOUND_EMERGENCY") else "On schedule"

    rows = [
        {
            "station_id": station_id,
            "item": "Critical spare parts resupply",
            "mode": "Aircraft (IL-76 sortie)",
            "expected_arrival": (now + timedelta(days=int(rng.uniform(10, 40)))).date().isoformat(),
            "cargo_priority": "High",
            "weather_dependency": weather_dependency,
            "route_status": route_status,
            "source": SOURCE,
            "data_status": config.SIMULATED_DEMO,
        },
        {
            "station_id": station_id,
            "item": "Annual bulk resupply (fuel + consumables)",
            "mode": "Vessel",
            "expected_arrival": (now + timedelta(days=int(rng.uniform(60, 150)))).date().isoformat(),
            "cargo_priority": "Medium",
            "weather_dependency": "High",
            "route_status": "Planned",
            "source": SOURCE,
            "data_status": config.SIMULATED_DEMO,
        },
    ]
    return pd.DataFrame(rows)


def generate_communication_status(station_id, scenario="NORMAL"):
    now = datetime.now(timezone.utc)
    if scenario in ("EXTREME_WEATHER", "COMPOUND_EMERGENCY"):
        status, pending = "Degraded", 14
    else:
        status, pending = "Online", 0
    return pd.DataFrame([{
        "station_id": station_id,
        "status": status,
        "last_sync": now.isoformat(timespec="seconds"),
        "pending_items": pending,
        "source": SOURCE,
        "data_status": config.SIMULATED_DEMO,
    }])
