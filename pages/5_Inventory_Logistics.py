"""
pages/5_Inventory_Logistics.py
Supply monitoring, shortage prediction, and resupply prioritization.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, status_pill, simulated_data_banner, provenance_badge

st.set_page_config(page_title="Inventory & Logistics — PolarOps AI", page_icon="📦", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
ensure_db()

st.markdown("## 📦 Inventory & Logistics")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

station = st.selectbox("Station", list(config.STATIONS.keys()))
sdata = result["stations"][station]

simulated_data_banner()

inv = sdata["inventory_df"].copy()
inv["days_remaining"] = inv["quantity"] / inv["daily_usage"].replace(0, np.nan)
inv["days_remaining"] = inv["days_remaining"].fillna(9999)
inv["buffer_days"] = inv["days_remaining"] - inv["lead_time_days"]


def status_for(row):
    if row["buffer_days"] < 0:
        return "CRITICAL"
    elif row["buffer_days"] < 15:
        return "WATCH"
    else:
        return "NORMAL"


inv["status"] = inv.apply(status_for, axis=1)

st.markdown("#### Supply Shortage Prediction")
cols = st.columns(len(inv))
for col, (_, row) in zip(cols, inv.iterrows()):
    with col:
        metric_card(row["item_name"], f"{row['days_remaining']:.0f}d left",
                    pill_label=row["status"],
                    help_text=f"Stock {row['quantity']:.0f} · usage {row['daily_usage']:.2f}/day · "
                              f"lead time {row['lead_time_days']:.0f}d")

st.markdown("#### Resupply Prioritization")
priority_df = inv.sort_values("buffer_days")
for i, (_, row) in enumerate(priority_df.iterrows(), start=1):
    reason = (
        f"Buffer shortfall of {abs(row['buffer_days']):.0f} days against resupply lead time"
        if row["buffer_days"] < 0 else
        f"Buffer of {row['buffer_days']:.0f} days against resupply lead time"
    )
    st.markdown(
        f"**Priority {i}: {row['item_name']}** ({row['criticality']}) &nbsp; "
        f"{status_pill(row['status'])} — {reason}",
        unsafe_allow_html=True,
    )

st.markdown("#### Stock levels")
fig = go.Figure()
fig.add_trace(go.Bar(x=inv["item_name"], y=inv["quantity"], name="Current stock",
                      marker_color="#4FC3F7"))
fig.add_trace(go.Bar(x=inv["item_name"], y=inv["min_stock"], name="Minimum stock",
                      marker_color="#EF6C00"))
fig.update_layout(
    barmode="group", height=340, margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor=config.COLORS["background"], plot_bgcolor=config.COLORS["background"],
    font_color=config.COLORS["text"], legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 🚚 Logistics")
log = sdata["logistics_df"]
for _, row in log.iterrows():
    dep_pill = "HIGH" if row["weather_dependency"] == "High" else "MEDIUM"
    st.markdown(f"""
    <div class="polar-card">
        <b>{row['item']}</b> — {row['mode']}<br>
        Expected arrival: {row['expected_arrival']} &nbsp; | &nbsp;
        Cargo priority: {row['cargo_priority']} &nbsp; | &nbsp;
        Weather dependency: {status_pill(dep_pill)}<br>
        Route status: {row['route_status']}
    </div>
    """, unsafe_allow_html=True)

st.caption(provenance_badge("SIMULATED_DEMO") +
           " Inventory levels and logistics schedules are illustrative, not real current operational data.",
           unsafe_allow_html=True)

st.markdown("### ⚠️ Inventory & Logistics Risk")
c1, c2 = st.columns(2)
with c1:
    ir = sdata["sub_risks"]["inventory"]
    metric_card("Inventory Risk", ir["score"], pill_label=ir["level"])
    st.caption(ir["explanation"])
with c2:
    lr = sdata["sub_risks"]["logistics"]
    metric_card("Logistics Risk", lr["score"], pill_label=lr["level"])
    st.caption(lr["explanation"])
