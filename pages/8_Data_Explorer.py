"""
pages/8_Data_Explorer.py
Lets users inspect raw source data directly, with explicit provenance for
every table (REAL_OBSERVED / REAL_REFERENCE / SIMULATED_DEMO / MODEL_PREDICTION).
"""

import streamlit as st
import pandas as pd

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, provenance_badge, render_sidebar
from src.database import db

st.set_page_config(page_title="Data Explorer — PolarOps AI", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
render_sidebar()
ensure_db()

st.markdown("## 🔎 Data Explorer")
st.caption("Inspect the exact data behind every dashboard number, with full provenance.")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

station = st.selectbox("Station", list(config.STATIONS.keys()))
sdata = result["stations"][station]

st.markdown("### Data source registry")
try:
    sources_df = db.read_table("data_sources")
    st.dataframe(sources_df, use_container_width=True, height=220)
except Exception:
    st.info("Run scripts/initialize_database.py to populate the data source registry.")

st.markdown("---")
st.markdown("### Live pipeline outputs for this run")

dataset_choice = st.selectbox("Dataset", [
    "Weather readings", "Equipment readings", "Energy readings",
    "Inventory", "Logistics", "Equipment anomaly results (model output)",
])

if dataset_choice == "Weather readings":
    df = sdata["weather_df"]
    st.markdown(provenance_badge(df["data_status"].iloc[0]), unsafe_allow_html=True)
    st.caption(sdata["weather_provenance"])
elif dataset_choice == "Equipment readings":
    df = sdata["equipment_df"]
    st.markdown(provenance_badge(df["data_status"].iloc[0] if not df.empty else "SIMULATED_DEMO"),
                unsafe_allow_html=True)
elif dataset_choice == "Energy readings":
    df = sdata["energy_df"]
    st.markdown(provenance_badge(df["data_status"].iloc[0]), unsafe_allow_html=True)
elif dataset_choice == "Inventory":
    df = sdata["inventory_df"]
    st.markdown(provenance_badge(df["data_status"].iloc[0]), unsafe_allow_html=True)
elif dataset_choice == "Logistics":
    df = sdata["logistics_df"]
    st.markdown(provenance_badge(df["data_status"].iloc[0]), unsafe_allow_html=True)
else:
    df = pd.DataFrame(sdata["anomaly_results"])
    st.markdown(provenance_badge("MODEL_PREDICTION"), unsafe_allow_html=True)

st.dataframe(df, use_container_width=True, height=420)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download this table as CSV", csv, file_name=f"{station}_{dataset_choice.replace(' ', '_')}.csv")

st.markdown("---")
st.markdown("### 🌐 Real-source ingestion")
st.markdown(f"""
**NCPOR / NPDC:** In **REAL DATA** mode the platform first uses an official local CSV
export at `data/raw/ncpor/{station.lower()}_aws.csv`; if absent, it requests the latest
published observation from the public NCPOR/NPDC station page.

**IMD Polar WRF:** Official forecast exports can be placed at
`data/raw/imd/{station.lower()}_polar_wrf.csv` (or `.json`). They are tagged
**REAL_FORECAST** and are kept separate from NCPOR observations.

Equipment, energy, inventory and logistics remain **SIMULATED_DEMO** unless an official
station telemetry feed is supplied. The platform never labels those simulated streams as real.
""")
