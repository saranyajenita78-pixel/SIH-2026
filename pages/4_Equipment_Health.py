"""
pages/4_Equipment_Health.py
Equipment monitoring + explainable predictive maintenance.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, status_pill, simulated_data_banner, provenance_badge

st.set_page_config(page_title="Equipment Health — PolarOps AI", page_icon="🛠️", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
ensure_db()

st.markdown("## 🛠️ Equipment Health & Predictive Maintenance")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

station = st.selectbox("Station", list(config.STATIONS.keys()))
sdata = result["stations"][station]

simulated_data_banner()

anomaly_results = sdata["anomaly_results"]
if not anomaly_results:
    st.warning("Equipment model output is unavailable for this run.")
    st.info("Internal station telemetry is not public, so the prototype generates SIMULATED_DEMO operational history for equipment/energy models. Restart the app after updating to this build.")
    st.stop()

sorted_results = sorted(anomaly_results, key=lambda r: r["anomaly_probability"], reverse=True)

st.markdown("#### Fleet overview")
cols = st.columns(len(sorted_results))
for col, r in zip(cols, sorted_results):
    with col:
        metric_card(r["equipment_id"], f"{r['health_pct']}%", pill_label=r["priority"],
                    help_text="Health score")

st.markdown("---")
st.markdown("#### Unit detail")
eq_id = st.selectbox("Select equipment", [r["equipment_id"] for r in sorted_results])
r = next(x for x in sorted_results if x["equipment_id"] == eq_id)
eq_meta = next(e for e in config.EQUIPMENT_LIST if e["id"] == eq_id)

k1, k2, k3 = st.columns(3)
with k1: metric_card("Equipment", eq_meta["name"])
with k2: metric_card("Health", f"{r['health_pct']}%", pill_label=r["priority"])
with k3: metric_card("Anomaly probability", r["anomaly_probability"], pill_label=r["priority"])

st.markdown(f"**Secondary model confirmation (IsolationForest):** "
            f"{'⚠️ Flagged as unusual' if r['iso_forest_flag'] else '✅ Not flagged'}")

st.markdown("##### 🔍 Why this assessment? (Explainable AI)")
st.markdown(f"""
<div class="polar-card">
<b>WHAT HAPPENED?</b><br>
Equipment <b>{eq_id}</b> currently shows a health score of <b>{r['health_pct']}%</b>
(anomaly probability {r['anomaly_probability']}).<br><br>
<b>WHY DID THE MODEL DETECT IT?</b><br>
{"".join(f"&bull; <b>{s['feature']}</b> is {s['direction']} for this unit's own recent baseline (z = {s['z_score']})<br>" for s in r['top_signals'])}
<br><b>WHAT SHOULD THE OPERATOR REVIEW?</b><br>
{"Inspect this unit's telemetry and schedule a maintenance check." if r['priority'] in ("HIGH", "CRITICAL") else "Continue routine monitoring."}
</div>
""", unsafe_allow_html=True)

eq_df = sdata["equipment_df"]
eq_df = eq_df[eq_df["equipment_id"] == eq_id].copy()
eq_df["timestamp"] = pd.to_datetime(eq_df["timestamp"])

fig = go.Figure()
fig.add_trace(go.Scatter(x=eq_df["timestamp"], y=eq_df["temperature_c"], name="Temperature (°C)",
                          line=dict(color="#EF6C00")))
fig.add_trace(go.Scatter(x=eq_df["timestamp"], y=eq_df["vibration_mm_s"], name="Vibration (mm/s)",
                          yaxis="y2", line=dict(color="#F44336")))
fig.add_trace(go.Scatter(x=eq_df["timestamp"], y=eq_df["load_pct"], name="Load (%)",
                          yaxis="y3", line=dict(color="#4FC3F7")))
fig.update_layout(
    height=380, margin=dict(l=10, r=60, t=10, b=10),
    paper_bgcolor=config.COLORS["background"], plot_bgcolor=config.COLORS["background"],
    font_color=config.COLORS["text"],
    yaxis=dict(title="°C"),
    yaxis2=dict(title="mm/s", overlaying="y", side="right"),
    yaxis3=dict(title="Load %", overlaying="y", side="right", position=0.95, showgrid=False),
    legend=dict(orientation="h", y=1.12),
)
st.plotly_chart(fig, use_container_width=True)
st.caption(provenance_badge("SIMULATED_DEMO") + " telemetry &nbsp;→&nbsp; " +
           provenance_badge("MODEL_PREDICTION") + " anomaly assessment", unsafe_allow_html=True)
