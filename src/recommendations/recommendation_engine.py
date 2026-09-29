"""
src/recommendations/recommendation_engine.py
Turns the current alert list + risk breakdown into a ranked, explainable
"what should the operator review first" list. Decision support only — never
presented as an official safety instruction (see config / README).
"""

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def generate_recommendations(station_id, alerts, overall_risk_result, timestamp):
    recs = []
    priority = 1
    for alert in alerts:
        recs.append({
            "station_id": station_id,
            "priority": priority,
            "title": f"Review {alert['category'].lower()} conditions ({alert['severity']})",
            "reason": alert["explanation"],
            "category": alert["category"],
            "timestamp": timestamp,
        })
        priority += 1

    if not alerts:
        recs.append({
            "station_id": station_id,
            "priority": 1,
            "title": "No immediate action required",
            "reason": f"Overall operational risk is {overall_risk_result['level']} "
                      f"({overall_risk_result['score']}/100). Continue routine monitoring.",
            "category": "General",
            "timestamp": timestamp,
        })

    return recs


def build_decision_card(station_id, overall_risk_result, alerts, recommendations):
    """Builds the single-glance 'Operational Decision Support' summary."""
    if not alerts:
        situation = "Normal operations"
        primary_risk = "None"
        secondary_risk = "None"
    else:
        situation = " + ".join(sorted({a["category"] for a in alerts[:3]}))
        primary_risk = alerts[0]["category"] if len(alerts) > 0 else "None"
        secondary_risk = alerts[1]["category"] if len(alerts) > 1 else "None"

    review_steps = [r["title"] for r in recommendations[:5]]

    return {
        "station_id": station_id,
        "current_situation": situation,
        "primary_risk": primary_risk,
        "secondary_risk": secondary_risk,
        "recommended_review": review_steps,
        "confidence": "Model-dependent — decision support only, not an official safety instruction.",
        "data_status": "Real environmental data where available + SIMULATED_DEMO operational telemetry "
                        "+ MODEL_PREDICTION risk/anomaly scores.",
        "overall_risk": overall_risk_result,
    }
