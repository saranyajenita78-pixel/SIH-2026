"""
pages/9_Model_Performance.py
Shows ML methodology, metrics and explicit limitations for every model used.
"""

import streamlit as st

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, provenance_badge, render_sidebar

st.set_page_config(page_title="Model Performance — PolarOps AI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
render_sidebar()
ensure_db()

st.markdown("## 📊 Model Performance")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

st.markdown("### 1. Equipment Anomaly Detection")
st.markdown("""
- **Purpose:** flag equipment units drifting away from their own recent "known-good" behaviour.
- **Method:** per-unit baseline (mean/std of temperature, vibration, load, voltage) learned from
  the earlier 60% of that unit's history; a smoothed multivariate z-score against this baseline
  is the primary risk signal, with an independent IsolationForest trained on the same baseline
  as a secondary confirmation flag.
- **Why not deep learning:** dataset per unit is small (hundreds of hourly readings); a
  transparent statistical baseline is more explainable and just as effective here.
- **Evaluation limitation:** there is no real, labeled equipment-failure ground truth for
  Antarctic station generators available to this project. Evaluation is therefore limited to
  unsupervised diagnostics (score separation between the deliberately-injected demo anomaly
  scenario and the normal baseline) rather than precision/recall — see below.
""")

station = st.selectbox("Station (for the diagnostic below)", list(config.STATIONS.keys()))
sdata = result["stations"][station]
if sdata["anomaly_results"]:
    st.markdown("**Current run — health scores by unit:**")
    for r in sdata["anomaly_results"]:
        metric_card(r["equipment_id"], f"{r['health_pct']}%", pill_label=r["priority"])

st.markdown("---")
st.markdown("### 2. Energy Consumption Forecast")
st.markdown("""
- **Purpose:** short-horizon (next-hour) energy consumption forecasting to support fuel/load planning.
- **Method:** RandomForestRegressor on lagged consumption (1, 2, 3, 6, 24h), a 6-hour rolling mean,
  and hour-of-day, compared against a naive previous-hour persistence baseline.
- **Validation:** time-aware split — the model is trained only on the earlier portion of the series
  and evaluated on the most recent held-out block. Data is never randomly shuffled across the
  train/test boundary, to avoid leaking future information into training.
- **Metrics used:** MAE, RMSE, R² (regression).
""")
fr = sdata.get("forecast_result")
if fr:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Baseline**")
        st.json(fr["baseline_metrics"])
    with c2:
        st.markdown("**Model**")
        st.json(fr["model_metrics"])
    st.caption("A lower MAE/RMSE and higher R² for the model vs. the baseline indicates the "
               "engineered features are adding predictive value beyond naive persistence.")
    if fr.get("next_hour_prediction_kw") is not None:
        st.metric("Next-hour consumption estimate", f"{fr['next_hour_prediction_kw']:.1f} kW", help="MODEL_PREDICTION from the final model fitted on the available simulated operational history.")
else:
    st.info("Forecast not available for the current scenario/history window.")

st.markdown("---")
st.markdown("### 3. Weather & Operational Risk Engine")
st.markdown("""
- **Purpose:** convert raw telemetry into a transparent, weighted 0–100 risk score per domain
  (weather, equipment, energy, inventory, logistics, communication) and an overall score.
- **Method:** rule-based, configurable thresholds and weights (see `config.py`), not a trained
  classifier — chosen deliberately for full explainability, since this score directly drives
  alerts and recommendations shown to operators.
- **Limitation:** thresholds are illustrative defaults appropriate for the simulated telemetry
  ranges in this prototype, not validated against real historical Antarctic incident data.
""")

st.markdown("---")
st.markdown("### Model outputs are always labeled")
st.markdown(provenance_badge("MODEL_PREDICTION") +
            " — every score, forecast, and anomaly probability on this dashboard carries this "
            "provenance tag and is treated as decision support, never a certainty.",
            unsafe_allow_html=True)
