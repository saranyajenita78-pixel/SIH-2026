"""
src/risk/risk_engine.py
Transparent, explainable operational risk engine.

Each domain produces a 0-100 sub-score with a plain-language explanation of
*why*. The overall score is a configurable weighted sum (config.RISK_WEIGHTS)
so every contribution is visible on the dashboard rather than hidden inside
a black-box number.
"""

import numpy as np
import pandas as pd

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


def _level_for(score):
    for lo, hi, label in config.RISK_LEVELS:
        if lo <= score < hi:
            return label
    return "CRITICAL"


def weather_risk(latest_weather_row, pressure_change_6h=0.0):
    t = latest_weather_row["temperature_c"]
    w = latest_weather_row["wind_speed_kmh"]
    th = config.WEATHER_THRESHOLDS

    # Colder conditions increase cold-stress risk; warmer-than-moderate
    # temperatures are not treated as a hazard by this prototype.
    if t <= th["temp_c_low"]:
        temp_contrib = 100.0
    elif t <= th["temp_c_moderate"]:
        span = max(1.0, th["temp_c_moderate"] - th["temp_c_low"])
        temp_contrib = 55.0 + 45.0 * ((th["temp_c_moderate"] - t) / span)
    else:
        temp_contrib = 0.0
    temp_contrib = float(np.clip(temp_contrib, 0, 100))

    wind_contrib = 0
    if w >= th["wind_kmh_high"]:
        wind_contrib = 100
    elif w >= th["wind_kmh_moderate"]:
        wind_contrib = 55
    else:
        wind_contrib = float(np.clip((w / th["wind_kmh_moderate"]) * 40, 0, 100))

    pressure_contrib = float(np.clip(
        (abs(pressure_change_6h) / th["pressure_hpa_change_high"]) * 100, 0, 100))

    score = 0.45 * wind_contrib + 0.40 * temp_contrib + 0.15 * pressure_contrib
    level = _level_for(score)

    factors = [
        {"factor": "Wind speed", "value": f"{w:.1f} km/h", "contribution": round(wind_contrib, 1)},
        {"factor": "Temperature", "value": f"{t:.1f} °C", "contribution": round(temp_contrib, 1)},
        {"factor": "Pressure change (6h)", "value": f"{pressure_change_6h:+.1f} hPa",
         "contribution": round(pressure_contrib, 1)},
    ]
    factors.sort(key=lambda f: f["contribution"], reverse=True)

    explanation = (
        f"Weather risk is {level} mainly due to {factors[0]['factor'].lower()} "
        f"({factors[0]['value']}), which is outside the historical operating "
        f"range used by the model."
        if score >= 25 else
        "Current weather conditions are within the normal operating envelope."
    )

    return {"score": round(score, 1), "level": level, "factors": factors, "explanation": explanation}


def equipment_risk(anomaly_results):
    """anomaly_results: list of dicts from src.ml.anomaly_detection.score_latest"""
    if not anomaly_results:
        return {"score": 0.0, "level": "LOW", "factors": [], "explanation": "No equipment telemetry available."}

    worst = max(anomaly_results, key=lambda r: r["anomaly_probability"])
    score = worst["anomaly_probability"] * 100
    level = _level_for(score)
    top_signal = worst["top_signals"][0] if worst["top_signals"] else None
    explanation = (
        f"Highest equipment risk is {worst['equipment_id']} "
        f"(health {worst['health_pct']}%, anomaly probability {worst['anomaly_probability']}). "
        + (f"Main contributing signal: {top_signal['feature']} is {top_signal['direction']}."
           if top_signal else "")
    )
    factors = [{"factor": r["equipment_id"], "value": f"health {r['health_pct']}%",
                "contribution": round(r["anomaly_probability"] * 100, 1)} for r in anomaly_results]
    factors.sort(key=lambda f: f["contribution"], reverse=True)
    return {"score": round(score, 1), "level": level, "factors": factors[:5], "explanation": explanation}


def energy_risk(latest_energy_row):
    fuel = latest_energy_row["fuel_level_pct"]
    load = latest_energy_row["generator_load_pct"]

    fuel_contrib = float(np.clip((100 - fuel) * 1.1, 0, 100)) if fuel < 40 else float(np.clip((40 - fuel), 0, 20))
    fuel_contrib = float(np.clip(fuel_contrib, 0, 100))
    load_contrib = float(np.clip((load - 70) * 2.5, 0, 100))

    score = 0.6 * fuel_contrib + 0.4 * load_contrib
    level = _level_for(score)
    factors = [
        {"factor": "Fuel level", "value": f"{fuel:.1f}%", "contribution": round(fuel_contrib, 1)},
        {"factor": "Generator load", "value": f"{load:.1f}%", "contribution": round(load_contrib, 1)},
    ]
    factors.sort(key=lambda f: f["contribution"], reverse=True)
    explanation = (
        f"Energy risk is {level}: {factors[0]['factor'].lower()} is {factors[0]['value']}."
        if score >= 25 else "Fuel reserves and generator load are within normal parameters."
    )
    return {"score": round(score, 1), "level": level, "factors": factors, "explanation": explanation}


def inventory_risk(inventory_df):
    """Computes days remaining per item; risk driven by the most urgent item."""
    if inventory_df.empty:
        return {"score": 0.0, "level": "LOW", "factors": [], "explanation": "No inventory data."}

    df = inventory_df.copy()
    df["days_remaining"] = df["quantity"] / df["daily_usage"].replace(0, np.nan)
    df["days_remaining"] = df["days_remaining"].fillna(9999)
    df["buffer_days"] = df["days_remaining"] - df["lead_time_days"]

    crit_weight = df["criticality"].map({
        "Very High": 1.0, "High": 0.7, "Medium": 0.4, "Low": 0.2
    }).fillna(0.4)

    df["item_score"] = np.clip((-df["buffer_days"] / 10.0) * 100 * crit_weight, 0, 100)

    worst = df.sort_values("item_score", ascending=False).iloc[0]
    score = float(worst["item_score"])
    level = _level_for(score)

    explanation = (
        f"{worst['item_name']} at {worst['station_id']} has an estimated "
        f"{worst['days_remaining']:.0f} days of stock remaining against a "
        f"{worst['lead_time_days']:.0f}-day resupply lead time "
        f"({'buffer of ' + format(worst['buffer_days'], '.0f') + ' days' if worst['buffer_days'] >= 0 else 'a shortfall of ' + format(-worst['buffer_days'], '.0f') + ' days'})."
        if score >= 25 else "All tracked items have adequate buffer against resupply lead times."
    )

    factors = [{"factor": f"{r.item_name} ({r.station_id})",
                "value": f"{r.days_remaining:.0f}d remaining / {r.lead_time_days:.0f}d lead time",
                "contribution": round(r.item_score, 1)}
               for r in df.sort_values("item_score", ascending=False).itertuples()]

    return {"score": round(score, 1), "level": level, "factors": factors[:5], "explanation": explanation}


def logistics_risk(logistics_df):
    if logistics_df.empty:
        return {"score": 0.0, "level": "LOW", "factors": [], "explanation": "No logistics data."}
    delayed = logistics_df[logistics_df["route_status"].str.contains("Delay", case=False, na=False)]
    score = 60.0 if len(delayed) > 0 else 10.0
    level = _level_for(score)
    explanation = (
        f"{len(delayed)} shipment(s) delayed due to closed weather windows."
        if len(delayed) > 0 else "Planned resupply movements are on schedule."
    )
    factors = [{"factor": r.item, "value": r.route_status, "contribution": 60.0 if "Delay" in r.route_status else 10.0}
               for r in logistics_df.itertuples()]
    return {"score": round(score, 1), "level": level, "factors": factors, "explanation": explanation}


def communication_risk(comm_row):
    status = comm_row["status"]
    score = {"Online": 5.0, "Degraded": 55.0, "Offline": 95.0}.get(status, 30.0)
    level = _level_for(score)
    explanation = f"Communication link status: {status}. {comm_row['pending_items']} item(s) pending sync."
    factors = [{"factor": "Link status", "value": status, "contribution": score}]
    return {"score": round(score, 1), "level": level, "factors": factors, "explanation": explanation}


def overall_risk(sub_risks: dict):
    """sub_risks keys must match config.RISK_WEIGHTS keys."""
    total = 0.0
    contributions = []
    for domain, weight in config.RISK_WEIGHTS.items():
        sub = sub_risks.get(domain, {"score": 0.0})
        contrib = sub["score"] * weight
        total += contrib
        contributions.append({"domain": domain, "score": sub["score"],
                               "weight": weight, "weighted_contribution": round(contrib, 1)})
    contributions.sort(key=lambda c: c["weighted_contribution"], reverse=True)
    level = _level_for(total)
    return {"score": round(total, 1), "level": level, "contributions": contributions}
