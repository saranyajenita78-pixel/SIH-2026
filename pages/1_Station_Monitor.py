"""
pages/1_Station_Monitor.py
Side-by-side and single-station monitoring view.
"""

import streamlit as st
import os, base64
import pandas as pd
import plotly.graph_objects as go
import os, base64

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, provenance_badge, render_sidebar, status_pill


STATION_IMAGES={}


def local_photo(station):
    path=os.path.join(config.BASE_DIR,"assets","stations",f"{station.lower()}_fallback.png")
    return path if os.path.exists(path) else None

st.set_page_config(page_title="Station Monitor — PolarOps AI", page_icon="🗺️", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
render_sidebar()
ensure_db()

st.markdown("## 🗺️ Station Monitor")
scenario = get_current_scenario()
st.caption(f"Demo scenario: **{scenario}**")

result = get_pipeline_result(scenario, get_current_data_mode())

selected = st.selectbox("Select station", list(config.STATIONS.keys()))
meta = config.STATIONS[selected]
sdata = result["stations"][selected]

c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Region", meta["region"])
with c2:
    metric_card("Coordinates", f"{meta['latitude']:.3f}, {meta['longitude']:.3f}")
with c3:
    metric_card("Established", meta["established"])
st.caption(provenance_badge("REAL_REFERENCE") + " — station identity/coordinates are public reference facts.",
           unsafe_allow_html=True)

st.markdown("---")
photo=local_photo(selected)
if photo:
    st.image(photo, caption=f"{selected} research station • reference photo")
else:
    st.info("Bundled station reference image is unavailable.")

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Overall Risk", sdata["overall_risk"]["score"], pill_label=sdata["overall_risk"]["level"])
with k2:
    latest_w = sdata["weather_df"].iloc[-1]
    metric_card("Latest Temp", f"{latest_w['temperature_c']:.1f} °C")
with k3:
    metric_card("Latest Wind", f"{latest_w['wind_speed_kmh']:.1f} km/h")
with k4:
    comm = sdata["communication"]
    metric_card("Communication", comm["status"], pill_label="OFFLINE" if comm["status"] == "Offline"
                else ("MEDIUM" if comm["status"] == "Degraded" else "LOW"))

st.markdown("#### Historical trend — Maitri vs Bharati")
metric_choice = st.radio("Variable", ["Temperature (°C)", "Wind speed (km/h)", "Pressure (hPa)"],
                          horizontal=True)
col_map = {"Temperature (°C)": "temperature_c", "Wind speed (km/h)": "wind_speed_kmh",
           "Pressure (hPa)": "pressure_hpa"}
col = col_map[metric_choice]

fig = go.Figure()
for sid, color in zip(config.STATIONS.keys(), ["#4FC3F7", "#F9A825"]):
    w = result["stations"][sid]["weather_df"].copy()
    w["timestamp"] = pd.to_datetime(w["timestamp"])
    fig.add_trace(go.Scatter(x=w["timestamp"], y=w[col], name=sid, line=dict(color=color)))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor=config.COLORS["background"], plot_bgcolor=config.COLORS["background"],
    font_color=config.COLORS["text"], yaxis_title=metric_choice,
    legend=dict(orientation="h", y=1.08),
)
st.plotly_chart(fig, use_container_width=True)
st.markdown(provenance_badge(sdata["weather_df"]["data_status"].iloc[0]), unsafe_allow_html=True)

st.markdown("#### Latest observations table")
st.dataframe(sdata["weather_df"].tail(24).sort_values("timestamp", ascending=False),
             use_container_width=True, height=300)
