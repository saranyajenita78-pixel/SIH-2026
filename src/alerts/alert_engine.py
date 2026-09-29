"""
src/alerts/alert_engine.py
Converts risk-engine outputs into a de-duplicated, prioritized alert list.
Only fires an alert when a domain's risk level is MEDIUM or above, to avoid
meaningless notification spam (per project requirements).
"""

from datetime import datetime, timezone

SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

CATEGORY_MAP = {
    "weather": "Environmental",
    "equipment": "Equipment",
    "energy": "Energy",
    "inventory": "Inventory",
    "logistics": "Logistics",
    "communication": "Communication",
}

RECOMMENDED_ACTIONS = {
    "Environmental": "Review latest AWS observations and postpone non-essential outdoor operations.",
    "Equipment": "Inspect the flagged unit's telemetry and schedule a maintenance check.",
    "Energy": "Verify fuel reserves and reduce non-critical generator load.",
    "Inventory": "Initiate resupply request and review consumption of the flagged item.",
    "Logistics": "Reassess shipment schedule and identify the next viable weather window.",
    "Communication": "Switch to backup communication procedure and queue data for sync.",
}


def generate_alerts(station_id, sub_risks: dict, timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")
    alerts = []
    for domain, sub in sub_risks.items():
        if sub["level"] in ("MEDIUM", "HIGH", "CRITICAL"):
            category = CATEGORY_MAP.get(domain, domain.title())
            alerts.append({
                "station_id": station_id,
                "category": category,
                "severity": sub["level"],
                "timestamp": timestamp,
                "trigger_text": sub["explanation"],
                "explanation": sub["explanation"],
                "recommended_action": RECOMMENDED_ACTIONS.get(category, "Review the affected module."),
                "status": "OPEN",
            })
    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 0), reverse=True)
    return alerts
