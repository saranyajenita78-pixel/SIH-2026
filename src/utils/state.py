"""
src/utils/state.py
Shared Streamlit session/cache helpers so every page (app.py + pages/*.py)
reads the exact same pipeline output for the currently selected Demo Mode
scenario, without recomputing it on every page switch.
"""

import streamlit as st

import config
from src.database import db
from src.pipeline import run_full_pipeline


@st.cache_resource
def ensure_db():
    db.initialize_database()
    db.seed_stations()
    return True


@st.cache_resource(ttl=900, show_spinner=False)
def get_pipeline_result(scenario, data_mode=None):
    """Keep one in-memory pipeline snapshot per scenario for 15 minutes.

    cache_resource avoids Streamlit serializing the large DataFrame-rich result
    on every page navigation. Pages treat the snapshot as read-only.
    """
    return run_full_pipeline(scenario=scenario, data_mode=data_mode)


def get_current_data_mode():
    """UI pages use the real-source pipeline; DEMO remains available only for tests/dev via config."""
    return "REAL"


def get_current_scenario():
    if "scenario" not in st.session_state:
        st.session_state.scenario = "NORMAL"
    return st.session_state.scenario


def scenario_sidebar_note():
    st.sidebar.caption(f"Demo scenario: **{get_current_scenario()}** "
                        f"(change it from the Command Center page)")
