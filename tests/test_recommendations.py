import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alerts import alert_engine
from src.recommendations import recommendation_engine


def _sub_risks(weather_level="LOW", equipment_level="CRITICAL"):
    return {
        "weather": {"score": 5.0, "level": weather_level, "explanation": "Calm conditions."},
        "equipment": {"score": 90.0, "level": equipment_level, "explanation": "Generator anomaly detected."},
        "energy": {"score": 10.0, "level": "LOW", "explanation": "Fuel and load normal."},
        "inventory": {"score": 10.0, "level": "LOW", "explanation": "Stock adequate."},
        "logistics": {"score": 10.0, "level": "LOW", "explanation": "On schedule."},
        "communication": {"score": 5.0, "level": "LOW", "explanation": "Link online."},
    }


def test_generate_alerts_only_fires_for_medium_plus():
    alerts = alert_engine.generate_alerts("Maitri", _sub_risks())
    categories = {a["category"] for a in alerts}
    assert "Equipment" in categories
    assert "Weather" not in categories  # LOW should not alert
    assert alerts[0]["severity"] == "CRITICAL"  # sorted by severity desc


def test_generate_alerts_none_when_all_low():
    sub_risks = _sub_risks(equipment_level="LOW")
    sub_risks["equipment"]["score"] = 5.0
    alerts = alert_engine.generate_alerts("Maitri", sub_risks)
    assert alerts == []


def test_recommendations_prioritize_alerts():
    alerts = alert_engine.generate_alerts("Maitri", _sub_risks())
    overall = {"score": 45.0, "level": "MEDIUM"}
    recs = recommendation_engine.generate_recommendations("Maitri", alerts, overall, "2024-01-01T00:00:00")
    assert recs[0]["priority"] == 1
    assert "equipment" in recs[0]["title"].lower()


def test_recommendations_no_action_when_no_alerts():
    overall = {"score": 5.0, "level": "LOW"}
    recs = recommendation_engine.generate_recommendations("Maitri", [], overall, "2024-01-01T00:00:00")
    assert len(recs) == 1
    assert "No immediate action" in recs[0]["title"]


def test_decision_card_reflects_top_alert():
    alerts = alert_engine.generate_alerts("Maitri", _sub_risks())
    overall = {"score": 45.0, "level": "MEDIUM"}
    recs = recommendation_engine.generate_recommendations("Maitri", alerts, overall, "2024-01-01T00:00:00")
    card = recommendation_engine.build_decision_card("Maitri", overall, alerts, recs)
    assert card["primary_risk"] == "Equipment"
    assert "Model-dependent" in card["confidence"]
