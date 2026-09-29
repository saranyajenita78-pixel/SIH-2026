"""
pages/2_Environment.py
Environmental / weather intelligence: time series, anomaly view, explainable
weather-risk breakdown.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, provenance_badge, render_sidebar, risk_factor_bars

st.set_page_config(page_title="Environment — PolarOps AI", page_icon="🌦️", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
render_sidebar()
ensure_db()

st.markdown("## 🌦️ Environment Monitoring")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

station = st.selectbox("Station", list(config.STATIONS.keys()))
sdata = result["stations"][station]
w = sdata["weather_df"].copy()
w["timestamp"] = pd.to_datetime(w["timestamp"])

date_range = st.slider("Days of history to show", 1, config.HISTORY_DAYS, config.HISTORY_DAYS)
w = w[w["timestamp"] >= w["timestamp"].max() - pd.Timedelta(days=date_range)]

st.markdown(provenance_badge(sdata["weather_df"]["data_status"].iloc[0]) +
            " &nbsp;" + sdata["weather_provenance"], unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
latest = w.iloc[-1]
with k1: metric_card("Temperature", f"{latest['temperature_c']:.1f} °C")
with k2: metric_card("Humidity", f"{latest['humidity_pct']:.0f} %")
with k3: metric_card("Pressure", f"{latest['pressure_hpa']:.1f} hPa")
with k4: metric_card("Wind speed", f"{latest['wind_speed_kmh']:.1f} km/h")

fig = make_subplots(rows=2, cols=2, subplot_titles=(
    "Temperature (°C)", "Wind speed (km/h)", "Pressure (hPa)", "Humidity (%)"))
fig.add_trace(go.Scatter(x=w["timestamp"], y=w["temperature_c"], line=dict(color="#4FC3F7")), row=1, col=1)
fig.add_trace(go.Scatter(x=w["timestamp"], y=w["wind_speed_kmh"], line=dict(color="#F9A825")), row=1, col=2)
fig.add_trace(go.Scatter(x=w["timestamp"], y=w["pressure_hpa"], line=dict(color="#AB47BC")), row=2, col=1)
fig.add_trace(go.Scatter(x=w["timestamp"], y=w["humidity_pct"], line=dict(color="#66BB6A")), row=2, col=2)
fig.update_layout(
    height=560, showlegend=False, margin=dict(l=10, r=10, t=40, b=10),
    paper_bgcolor=config.COLORS["background"], plot_bgcolor=config.COLORS["background"],
    font_color=config.COLORS["text"],
)
st.plotly_chart(fig, use_container_width=True)

# IMD forecast comparison when an official export has been supplied.
forecast_df = sdata.get("imd_forecast_df", pd.DataFrame()).copy()
if not forecast_df.empty:
    st.markdown("### 🔮 IMD Polar WRF Forecast")
    st.markdown(provenance_badge("REAL_FORECAST") + " &nbsp;" + sdata.get("imd_provenance", ""), unsafe_allow_html=True)
    forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"], utc=True)
    fc_cols = [c for c in ["timestamp", "temperature_c", "humidity_pct", "pressure_hpa", "wind_speed_kmh"] if c in forecast_df.columns]
    st.dataframe(forecast_df[fc_cols].sort_values("timestamp"), use_container_width=True, height=260)
else:
    st.info("No official IMD Polar WRF export is loaded for this station. See Data Explorer for the expected file format.")

st.markdown("---")
st.markdown("### ⚠️ Explainable Weather Risk")
wr = sdata["sub_risks"]["weather"]
c1, c2 = st.columns([1, 2])
with c1:
    metric_card("Weather Risk", wr["score"], pill_label=wr["level"])
    st.markdown(f"**Why:** {wr['explanation']}")
with c2:
    risk_factor_bars(wr["factors"], title="Contributing factors")

st.markdown("### Data table")
st.dataframe(w.sort_values("timestamp", ascending=False), use_container_width=True, height=320)
