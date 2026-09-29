"""
pages/6_Risk_Alerts.py
Consolidated operational risk breakdown and alert feed across both stations.
"""

import streamlit as st

import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, metric_card, render_sidebar, risk_factor_bars, risk_gauge, status_pill

st.set_page_config(page_title="Risk & Alerts — PolarOps AI", page_icon="🚨", layout="wide", initial_sidebar_state="expanded")
inject_base_css()
render_sidebar()
ensure_db()

st.markdown("## 🚨 Operational Risk & Alerts")
scenario = get_current_scenario()
result = get_pipeline_result(scenario, get_current_data_mode())

tabs = st.tabs(list(config.STATIONS.keys()))
for tab, sid in zip(tabs, config.STATIONS.keys()):
    sdata = result["stations"][sid]
    with tab:
        g1, g2 = st.columns([1, 1.4])
        with g1:
            risk_gauge(sdata["overall_risk"]["score"], title=f"{sid} Overall Risk")
        with g2:
            risk_factor_bars(sdata["overall_risk"]["contributions"], title="Weighted domain contribution")

        st.markdown("#### Domain breakdown")
        domain_cols = st.columns(6)
        domain_order = ["weather", "equipment", "energy", "inventory", "logistics", "communication"]
        for col, domain in zip(domain_cols, domain_order):
            sub = sdata["sub_risks"][domain]
            with col:
                metric_card(domain.title(), sub["score"], pill_label=sub["level"])

        st.markdown("#### Active Alerts")
        if not sdata["alerts"]:
            st.success("No active alerts — all domains within normal operating parameters.")
        for a in sdata["alerts"]:
            st.markdown(f"""
            <div class="polar-card">
                {status_pill(a['severity'])} &nbsp; <b>{a['category']}</b>
                &nbsp;·&nbsp; {a['timestamp']}<br><br>
                <b>Trigger:</b> {a['trigger_text']}<br>
                <b>Recommended action:</b> {a['recommended_action']}<br>
                <b>Status:</b> {a['status']}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### Recommendations (priority order)")
        for r in sdata["recommendations"]:
            st.markdown(f"**{r['priority']}. {r['title']}** — {r['reason']}")
