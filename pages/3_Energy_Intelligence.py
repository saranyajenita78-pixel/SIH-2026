"""
pages/3_Energy_Intelligence.py
Energy monitoring + forecasting (baseline vs model comparison).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, provenance_badge, render_sidebar, risk_factor_bars, simulated_data_banner

st.set_page_config(page_title="Energy Intelligence — PolarOps AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
render_sidebar()
ensure_db()

st.markdown("## ⚡ Energy Intelligence")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

station = st.selectbox("Station", list(config.STATIONS.keys()))
sdata = result["stations"][station]
e = sdata["energy_df"].copy()
e["timestamp"] = pd.to_datetime(e["timestamp"])

simulated_data_banner()

latest = e.iloc[-1]
k1, k2, k3, k4 = st.columns(4)
with k1: metric_card("Production", f"{latest['production_kw']:.0f} kW")
with k2: metric_card("Consumption", f"{latest['consumption_kw']:.0f} kW")
with k3: metric_card("Generator Load", f"{latest['generator_load_pct']:.0f} %")
with k4: metric_card("Fuel Level", f"{latest['fuel_level_pct']:.1f} %",
                      pill_label="CRITICAL" if latest["fuel_level_pct"] < 20 else
                      ("HIGH" if latest["fuel_level_pct"] < 40 else "LOW"))

fig = go.Figure()
fig.add_trace(go.Scatter(x=e["timestamp"], y=e["production_kw"], name="Production (kW)",
                          line=dict(color="#66BB6A")))
fig.add_trace(go.Scatter(x=e["timestamp"], y=e["consumption_kw"], name="Consumption (kW)",
                          line=dict(color="#EF6C00")))
fig.add_trace(go.Scatter(x=e["timestamp"], y=e["fuel_level_pct"], name="Fuel level (%)",
                          yaxis="y2", line=dict(color="#4FC3F7", dash="dot")))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor=config.COLORS["background"], plot_bgcolor=config.COLORS["background"],
    font_color=config.COLORS["text"],
    yaxis=dict(title="kW"), yaxis2=dict(title="Fuel %", overlaying="y", side="right", range=[0, 100]),
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 🔮 Energy Consumption Forecast — Baseline vs Model")
fr = sdata["forecast_result"]
if fr is None:
    st.info("Not enough history to train a reliable forecast for this scenario window.")
else:
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("**Baseline (previous-hour persistence)**")
        st.json(fr["baseline_metrics"])
    with m2:
        st.markdown("**Model (Random Forest, time-aware split)**")
        st.json(fr["model_metrics"])

    rdf = fr["result_df"]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["actual_kw"], name="Actual", line=dict(color="#4FC3F7")))
    fig2.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["baseline_pred_kw"], name="Baseline prediction",
                               line=dict(color="#9AA4B2", dash="dot")))
    fig2.add_trace(go.Scatter(x=rdf["timestamp"], y=rdf["model_pred_kw"], name="Model prediction",
                               line=dict(color="#F9A825")))
    fig2.update_layout(
        height=360, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=config.COLORS["background"], plot_bgcolor=config.COLORS["background"],
        font_color=config.COLORS["text"], yaxis_title="kW",
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(provenance_badge("MODEL_PREDICTION") +
               " Forecast shown is on a held-out, time-ordered test window (never shuffled with training data).",
               unsafe_allow_html=True)

st.markdown("---")
st.markdown("### ⚠️ Energy Risk")
er = sdata["sub_risks"]["energy"]
c1, c2 = st.columns([1, 2])
with c1:
    metric_card("Energy Risk", er["score"], pill_label=er["level"])
    st.markdown(f"**Why:** {er['explanation']}")
with c2:
    risk_factor_bars(er["factors"], title="Contributing factors")
