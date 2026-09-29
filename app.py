"""Polar Twin Sentinel — immersive command center."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, re, base64

import config
from src.utils.state import ensure_db, get_pipeline_result
from src.utils.ui_helpers import inject_base_css, provenance_badge, render_sidebar, status_pill
from src.ai.copilot import ask as ask_real_ai, is_configured as real_ai_configured

st.set_page_config(page_title="Polar Twin Sentinel", page_icon="🧊", layout="wide", initial_sidebar_state="expanded")
inject_base_css(); ensure_db()
render_sidebar()

# Bundled station reference images. No remote image hosts are used, so the dashboard
# remains stable even when the machine has no internet connection.
def station_image_url(station_id):
    """Return a local bundled PNG as a data URI."""
    path = os.path.join(config.BASE_DIR, "assets", "stations", f"{station_id.lower()}_fallback.png")
    if not os.path.exists(path):
        path = os.path.join(config.BASE_DIR, "assets", "stations", f"{station_id.lower()}_fallback.svg")
    ext = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/svg+xml"
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode("ascii")

try:
    result=get_pipeline_result(st.session_state.scenario, "REAL")
except RuntimeError as exc:
    st.error(str(exc))
    st.info("REAL mode is strict: the dashboard shows only verified NCPOR observations (or a previously cached real observation). No synthetic weather is substituted when the source is unavailable.")
    st.stop()

stations=result["stations"]

# HERO
st.markdown('''<div class="pts-hero"><div class="hero-top"><div><div class="pts-kicker">INDIAN ANTARCTIC OPERATIONS</div><div class="pts-title">POLAR TWIN <span>SENTINEL</span></div><div class="pts-sub">One command surface for Maitri and Bharati — observe the real environment, predict risk, test what-if situations, and act with human approval.</div></div><div class="hero-slogan">Science today<br><em>for a better tomorrow</em></div></div><div class="hero-bottom"><span class="pts-live"><span class="pts-dot"></span> LATEST NCPOR</span><span class="hero-note">NCPOR observations + IMD forecast + AI/ML + synthetic operational telemetry</span></div></div>''',unsafe_allow_html=True)

# compact operational status ribbon — keeps the dashboard informative without a REAL/DEMO switch
st.markdown(f'''<div class="status-grid">
  <div class="status-box"><div class="status-icon">⌂</div><div><div class="status-label">Stations</div><div class="status-value">2 Stations</div><div class="status-sub">Maitri + Bharati</div></div></div>
  <div class="status-box"><div class="status-icon">☁</div><div><div class="status-label">Station Weather</div><div class="status-value">2 Published</div><div class="status-sub">NCPOR observations</div></div></div>
  <div class="status-box"><div class="status-icon">✦</div><div><div class="status-label">Current Scenario</div><div class="status-value">{result["scenario"].replace("_"," ")}</div><div class="status-sub">No active alerts</div></div></div>
  <div class="status-box"><div class="status-icon">◉</div><div><div class="status-label">Decision Loop</div><div class="status-value">Observe → Predict → Prevent</div><div class="status-sub">AI-assisted • human approval</div></div></div>
</div>''' , unsafe_allow_html=True)

st.markdown("### 🛰️ Antarctic Station Twin")
cols=st.columns(2,gap="large")
for col,(sid,sdata) in zip(cols,stations.items()):
    with col:
        w=sdata["weather_df"].copy(); latest=w.iloc[-1]
        risk=sdata["overall_risk"]
        status="ATTENTION" if risk["level"] in ("HIGH","CRITICAL") else "OPERATIONAL"
        photo=station_image_url(sid)
        fallback=station_image_url(sid)
        try:
            obs_ts = pd.to_datetime(latest["timestamp"], utc=True)
            age_h = max(0.0, (pd.Timestamp.now(tz="UTC") - obs_ts).total_seconds() / 3600.0)
            freshness = "Latest published" if age_h <= 6 else f"Published {age_h:.0f}h ago"
        except Exception:
            freshness = "Timestamp unavailable"
        html=f'''<div class="station-card"><div class="station-photo-wrap"><img class="station-photo" src="{photo}" alt="{sid} Research Station" onerror="this.onerror=null;this.src='{fallback}';"><div class="photo-shade"></div><div class="photo-live"><i></i> {freshness.upper()}</div></div><div class="station-content"><div class="station-head"><div><div class="station-name">{sid} Research Station</div><div class="station-meta">{config.STATIONS[sid]['region']}</div></div><div>{provenance_badge(sdata["weather_df"]["data_status"].iloc[0])}</div></div><div class="station-metrics"><div class="station-metric"><label>Temperature</label><b>{latest['temperature_c']:.1f}°C</b><span>{freshness}</span></div><div class="station-metric"><label>Humidity</label><b>{latest['humidity_pct']:.0f}%</b><span>{freshness}</span></div><div class="station-metric"><label>Pressure</label><b>{latest['pressure_hpa']:.1f} hPa</b><span>{freshness}</span></div><div class="station-metric"><label>Wind Speed</label><b>{latest['wind_speed_kmh']:.1f} km/h</b><span>{freshness}</span></div></div></div></div>'''
        st.markdown(html,unsafe_allow_html=True)
        p1,p2=st.columns(2)
        with p1:
            with st.popover("▣ Open live station data",use_container_width=True):
                st.markdown(f"### {sid} telemetry")
                st.markdown(provenance_badge(sdata["weather_df"]["data_status"].iloc[0]),unsafe_allow_html=True)
                st.caption(sdata["weather_provenance"])
                st.metric("Risk",f"{risk['score']}/100")
                st.metric("Alerts",len(sdata["alerts"]))
                st.dataframe(w.tail(12),use_container_width=True,height=280)
        with p2:
            with st.popover("✦ Station intelligence",use_container_width=True):
                st.markdown(f"### {sid} decision brief")
                st.write(sdata["decision_card"]["current_situation"])
                st.write(f"**Primary risk:** {sdata['decision_card']['primary_risk']}")
                for rec in sdata["recommendations"][:3]: st.write(f"**{rec['priority']}. {rec['title']}** — {rec['reason']}")
                st.caption(f"Confidence: {sdata['decision_card']['confidence']}")

# VISUAL OPERATIONS STRIP — same pipeline data, rendered as real Streamlit cards
map_col, trend_col, alert_col = st.columns([1.05, 1.45, 1.0], gap="medium")

with map_col:
    with st.container(border=True):
        h1, h2 = st.columns([1, 0.7])
        with h1:
            st.markdown("**Antarctic Map**")
        with h2:
            st.markdown("<div style='text-align:right;color:#46d9ff;font-size:.72rem;font-weight:800'>STATION LOCATIONS</div>", unsafe_allow_html=True)
        # Actual geographic Plotly map (not an image). Coordinates come from config.
        geo = go.Figure()
        coords = {sid: config.STATIONS[sid] for sid in stations}
        lats = [float(coords[sid].get("latitude", coords[sid].get("lat", 0))) for sid in stations]
        lons = [float(coords[sid].get("longitude", coords[sid].get("lon", 0))) for sid in stations]
        names = list(stations.keys())
        geo.add_trace(go.Scattergeo(
            lat=lats, lon=lons, text=names, mode="markers+text",
            textposition="top center", textfont=dict(size=11, color="#eaf9ff"),
            marker=dict(size=10, color="#ff5f6d", line=dict(width=2, color="#ffffff")),
            hovertemplate="<b>%{text}</b><br>%{lat:.2f}°S<br>%{lon:.2f}°E<extra></extra>"
        ))
        # Research route between the two stations for orientation.
        geo.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines", line=dict(width=2, color="#55bfff", dash="dot"), hoverinfo="skip", showlegend=False))
        geo.update_geos(
            projection_type="stereographic", projection_rotation=dict(lat=-90, lon=0, roll=0),
            center=dict(lat=-90, lon=0), showland=True, landcolor="#dcecf5",
            showocean=True, oceancolor="#0b2944", showcountries=True,
            countrycolor="#7fa9c0", showcoastlines=True, coastlinecolor="#ffffff",
            coastlinewidth=0.8, lataxis_showgrid=True, lonaxis_showgrid=True,
            lataxis_gridcolor="#47718a", lonaxis_gridcolor="#47718a",
            bgcolor="rgba(0,0,0,0)"
        )
        geo.update_layout(height=235, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", geo=dict(bgcolor="rgba(0,0,0,0)"), showlegend=False)
        st.plotly_chart(geo, use_container_width=True, config={"displayModeBar": False})
        st.markdown("<div style='display:flex;justify-content:space-between;font-size:.62rem;color:#82a8c0'><span>🟢 Live station</span><span>🔴 Station location</span><span>┄ Research route</span></div>", unsafe_allow_html=True)

with trend_col:
    with st.container(border=True):
        h1, h2 = st.columns([1, 0.7])
        with h1:
            st.markdown("**Live Environmental Trends**")
        with h2:
            st.markdown("<div style='text-align:right;color:#46d9ff;font-size:.72rem;font-weight:800'>(NCPOR)</div>", unsafe_allow_html=True)
        fig = go.Figure()
        for sid, line_color in [("Maitri", "#22d3ee"), ("Bharati", "#60a5fa")]:
            df = stations[sid]["weather_df"].tail(12)
            fig.add_trace(go.Scatter(x=df.index, y=df["temperature_c"], mode="lines+markers", name=sid, line=dict(width=2, color=line_color), marker=dict(size=4)))
        fig.update_layout(height=235, margin=dict(l=10,r=8,t=8,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cceeff", legend=dict(orientation="h", y=1.08, x=0), xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(gridcolor="#173c5a", title="°C", title_font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with alert_col:
    with st.container(border=True):
        h1, h2 = st.columns([1, 0.55])
        with h1:
            st.markdown("**Recent Alerts**")
        with h2:
            st.markdown("<div style='text-align:right;color:#46d9ff;font-size:.72rem;font-weight:800'>LIVE-DERIVED</div>", unsafe_allow_html=True)
        alert_items=[]
        for sid, sdata in stations.items():
            for a in (sdata.get("alerts") or [])[:2]:
                latest=sdata["weather_df"].iloc[-1]
                alert_items.append((sid, a.get("title","Operational alert"), a.get("severity","INFO"), latest))
        if not alert_items:
            st.success("All Systems Nominal")
            st.caption("No decision-support threshold is currently triggered by the live observations.")
        else:
            for sid,title,severity,latest in alert_items[:3]:
                icon = "⚠️" if severity in ("HIGH","CRITICAL") else "ℹ️"
                st.markdown(f"<div class='alert-row'><div class='alert-icon'>{icon}</div><div><b>{title}</b><small>{sid} • Live NCPOR observation • {latest['wind_speed_kmh']:.1f} km/h wind</small></div></div>", unsafe_allow_html=True)
        st.caption("Source: NCPOR live observation • decision-support rule. Not an official NCPOR alert.")

# QUICK ACCESS — presentation-only shortcuts; existing page navigation remains unchanged.
quick_items=[("◈","Station Monitor","pages/1_Station_Monitor.py"),("⚡","Energy","pages/3_Energy_Intelligence.py"),("⚙","Equipment Health","pages/4_Equipment_Health.py"),("▣","Inventory & Logistics","pages/5_Inventory_Logistics.py"),("◇","What-If Simulation","pages/10_What_If_Simulation.py"),("✦","AI Insights","pages/7_AI_Insights.py"),("⌁","Data Explorer","pages/8_Data_Explorer.py")]
qcols=st.columns(len(quick_items), gap="small")
for c,(ic,label,target) in zip(qcols,quick_items):
    with c:
        st.page_link(target, label=f"{ic} {label}")

# DIGITAL TWIN FLOW
st.markdown("### 🧬 Digital Twin Control Loop")
st.markdown('<div class="panel"><div class="flow"><span class="flow-step">NCPOR REAL OBSERVATIONS</span><span class="flow-arrow">→</span><span class="flow-step">IMD POLAR WRF</span><span class="flow-arrow">→</span><span class="flow-step">VALIDATE & FUSE</span><span class="flow-arrow">→</span><span class="flow-step">DIGITAL TWIN</span><span class="flow-arrow">→</span><span class="flow-step">AI / ML</span><span class="flow-arrow">→</span><span class="flow-step">WHAT-IF</span><span class="flow-arrow">→</span><span class="flow-step">ALERT + ACTION</span></div></div>',unsafe_allow_html=True)

# AI COPILOT
st.markdown("### 🌐 Trusted Data Fabric")
source_cols=st.columns(4)
for c,(title,badge,desc) in zip(source_cols,[("NCPOR","REAL_OBSERVED","Published station observations"),("IMD Polar WRF","REAL_FORECAST","Official forecast export stream"),("Operational telemetry","SIMULATED_DEMO","Equipment / energy / logistics prototype data"),("AI / ML","MODEL_PREDICTION","Risk, anomaly and forecast outputs")]):
    with c: st.markdown(f'<div class="source-card"><div class="source-title">{title}</div><div style="margin:7px 0">{provenance_badge(badge)}</div><div class="source-copy">{desc}</div></div>',unsafe_allow_html=True)

st.markdown("### ✦ AI Operations Copilot")
qcol,acol=st.columns([1,1.4])
with qcol:
    quick=st.selectbox("Ask the twin",["What is the current station condition?","Which station has higher risk?","Which equipment needs attention?","What is the current power consumption?","What resources are becoming critical?","What is the IMD forecast status?","What should the team review first?","What changed recently?","How is the environment trending?","Will it work offline?"])
    ask=st.text_input("Or type your own question",placeholder="e.g. What is the biggest risk at Bharati?",key="home_ai_input")
    ask_now=st.button("✦ ASK AI",use_container_width=True,key="home_ai_button")

def answer_question(q):
    q=(q or "").strip().lower()
    if not q:
        return "Type a question and press ASK AI."
    # Station-specific context
    station_id = "Bharati" if "bharati" in q else ("Maitri" if "maitri" in q else None)
    selected_stations = {station_id: stations[station_id]} if station_id else stations
    if any(k in q for k in ["higher risk","worst risk","highest risk","risk first","risk level"]):
        sid=max(selected_stations,key=lambda x:selected_stations[x]['overall_risk']['score']); s=selected_stations[sid]
        dom=max(s['sub_risks'],key=lambda k:s['sub_risks'][k]['score'])
        return f"**{sid}** currently has the highest operational risk at **{s['overall_risk']['score']}/100 ({s['overall_risk']['level']})**. Largest contributing domain: **{dom.title()}**. Human review is required before any important action."
    if any(k in q for k in ["current station condition","station condition","current weather","weather now","status"]):
        return "\n\n".join([f"**{sid}** — **{s['weather_df'].iloc[-1]['temperature_c']:.1f}°C**, {s['weather_df'].iloc[-1]['humidity_pct']:.0f}% RH, {s['weather_df'].iloc[-1]['pressure_hpa']:.1f} hPa, wind {s['weather_df'].iloc[-1]['wind_speed_kmh']:.1f} km/h. Risk: **{s['overall_risk']['score']}/100**." for sid,s in selected_stations.items()])
    if any(k in q for k in ["temperature","humidity","pressure","wind"]):
        out=[]
        for sid,s in selected_stations.items():
            w=s['weather_df'].iloc[-1]
            out.append(f"**{sid}:** temperature {w['temperature_c']:.1f}°C • humidity {w['humidity_pct']:.0f}% • pressure {w['pressure_hpa']:.1f} hPa • wind {w['wind_speed_kmh']:.1f} km/h.")
        return "\n\n".join(out)
    if any(k in q for k in ["ncp","real data","observation","source"]):
        return "\n\n".join([f"**{sid}:** {s['weather_df'].iloc[-1]['source']} → **{s['weather_df'].iloc[-1]['data_status']}**. {s['weather_provenance']}" for sid,s in selected_stations.items()])
    if any(k in q for k in ["imd","forecast"]):
        return "\n\n".join([f"**{sid}:** {len(s.get('imd_forecast_df',[]))} IMD Polar WRF row(s) loaded." if not s.get('imd_forecast_df',pd.DataFrame()).empty else f"**{sid}:** IMD Polar WRF adapter is ready, but no official forecast export is loaded. The prototype does **not invent forecast values**." for sid,s in selected_stations.items()])
    if any(k in q for k in ["equipment","maintenance","machine"]):
        vals=[(r['anomaly_probability'],sid,r) for sid,s in selected_stations.items() for r in s['anomaly_results']]
        if vals:
            _,sid,r=max(vals,key=lambda x:x[0]); return f"**{r['equipment_id']} at {sid}** needs the most attention: health **{r['health_pct']}%**, anomaly probability **{r['anomaly_probability']}**, priority **{r['priority']}**. Telemetry is **SIMULATED_DEMO** for the prototype."
    if any(k in q for k in ["energy","power","fuel"]):
        return "\n\n".join([f"**{sid}:** consumption **{s['energy_df'].iloc[-1]['consumption_kw']:.0f} kW**, generator load {s['energy_df'].iloc[-1]['generator_load_pct']:.0f}%, fuel {s['energy_df'].iloc[-1]['fuel_level_pct']:.1f}%. **SIMULATED_DEMO**." for sid,s in selected_stations.items()])
    if any(k in q for k in ["inventory","resource","supply","logistics"]):
        out=[]
        for sid,s in selected_stations.items():
            inv=s['inventory_df'].copy(); inv['days_left']=inv['quantity']/inv['daily_usage'].replace(0,float('nan')); row=inv.sort_values('days_left').iloc[0]
            out.append(f"**{sid}:** {row['item_name']} has about **{row['days_left']:.0f} days** remaining vs **{row['lead_time_days']:.0f} days** lead time.")
        return "\n\n".join(out)
    if "what if" in q or "simulation" in q:
        m=re.search(r"wind[^0-9]*(\d+(?:\.\d+)?)",q)
        increase=float(m.group(1)) if m else 50.0
        sid=station_id or max(stations,key=lambda x:stations[x]['overall_risk']['score'])
        base=stations[sid]['overall_risk']['score']; projected=min(100,round(base+increase*.22)); level="CRITICAL" if projected>=75 else "HIGH" if projected>=50 else "MEDIUM" if projected>=25 else "LOW"
        return f"For **{sid}**, a **+{increase:.0f} km/h wind** shock moves projected risk from **{base}/100** to **{projected}/100 ({level})**. Open **What-If Mission Lab** to test the full weather + equipment + energy + logistics combination."
    if any(k in q for k in ["offline","connectivity"]):
        return "Yes. The platform is designed for offline-first operation: latest NCPOR observations can be cached locally, and synthetic operational telemetry remains available during connectivity loss. Data freshness and provenance remain visible."
    if any(k in q for k in ["recommend","action","should","review","prevent"]):
        return "\n\n".join([f"**{sid}:** {s['recommendations'][0]['title'] if s['recommendations'] else 'Continue routine monitoring.'} — **human approval required**." for sid,s in selected_stations.items()])
    return "I can answer about **NCPOR observations, IMD forecast status, station condition, temperature, risk, equipment, energy, inventory, logistics, what-if scenarios and offline readiness**. Try: *What is the biggest risk at Bharati?*"

with acol:
    if real_ai_configured():
        st.caption("AI Agent: OpenAI connected • conversational answers + optional web search")
    else:
        st.caption("AI Agent: not connected • local grounded copilot active (add OPENAI_API_KEY for full agent mode)")
    st.markdown('<div class="ai-box"><div class="panel-title">DECISION SUPPORT • GROUNDED IN CURRENT PIPELINE</div><h3>Ask the station twin</h3><div class="small-muted">The copilot answers from current NCPOR weather, model outputs, risk engine and simulated operational telemetry. It does not invent missing facts.</div>',unsafe_allow_html=True)
    question = ask if ask.strip() else quick
    if ask_now:
        real = ask_real_ai(question, result)
        st.session_state["home_ai_answer"] = real["text"] if real["mode"] == "OPENAI_AGENT" else answer_question(question)
        st.session_state["home_ai_mode"] = real["mode"]
        st.session_state["home_ai_web"] = real.get("used_web", False)
    elif "home_ai_answer" not in st.session_state:
        st.session_state["home_ai_answer"] = answer_question(question)
        st.session_state["home_ai_mode"] = "LOCAL_FALLBACK"
        st.session_state["home_ai_web"] = False
    mode_label = "OPENAI AI AGENT" if st.session_state.get("home_ai_mode") == "OPENAI_AGENT" else "LOCAL GROUNDED FALLBACK"
    web_label = " • WEB SEARCH USED" if st.session_state.get("home_ai_web") else ""
    st.caption(f"Assistant: {mode_label}{web_label}")
    st.markdown(f'<div class="answer">{st.session_state["home_ai_answer"].replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# HUMAN-IN-THE-LOOP APPROVAL
st.markdown('### 🛡️ Human Approval Gate')
a1,a2,a3=st.columns(3)
with a1:
    if st.button('Review highest-risk station',use_container_width=True): st.session_state['review_ack']=True
with a2:
    if st.button('Acknowledge recommendations',use_container_width=True): st.session_state['recommend_ack']=True
with a3:
    st.metric('Control authority','HUMAN ONLY')
if st.session_state.get('review_ack') or st.session_state.get('recommend_ack'):
    st.success('Review recorded locally. No physical station action is executed by this prototype.')

# WHAT-IF PREVIEW
st.markdown("### ◇ What-If Mission Lab")
st.markdown('<div class="whatif"><div class="panel-title">TEST BEFORE YOU ACT</div><div style="color:#dff7ff;font-size:1.05rem;font-weight:800">Simulate a weather + equipment shock and see the projected operational risk.</div></div>',unsafe_allow_html=True)
wc1,wc2,wc3,wc4=st.columns(4)
with wc1: temp_delta=st.slider("Temperature shift (°C)",-15,10,0)
with wc2: wind_delta=st.slider("Wind increase (km/h)",0,100,0)
with wc3: pressure_drop=st.slider("Pressure drop (hPa)",0,40,0)
with wc4: equipment_hit=st.slider("Equipment stress (%)",0,100,0)
base=max(s["overall_risk"]["score"] for s in stations.values()); scenario_score=min(100,round(base + abs(temp_delta)*1.0 + wind_delta*.22 + pressure_drop*.65 + equipment_hit*.20))
left,right=st.columns([1,2])
with left: st.metric("Projected peak risk",f"{scenario_score}/100",f"{scenario_score-base:+.0f} vs current peak")
with right:
    if scenario_score>=75: msg="CRITICAL: pre-emptive review recommended before operational action."
    elif scenario_score>=50: msg="HIGH: prepare mitigation and human approval."
    elif scenario_score>=25: msg="MEDIUM: increase monitoring and verify forecasts."
    else: msg="LOW: conditions remain within the current operating envelope."
    st.markdown(f'<div class="answer"><b>Simulation outcome:</b> {msg}<br><span class="small-muted">This is a prototype what-if calculation, not an autonomous control command.</span></div>',unsafe_allow_html=True)

# DATA FABRIC
st.markdown("### ◈ Trusted Data Fabric")
s1,s2,s3,s4=st.columns(4)
source_cards=[
("🌐","NCPOR / NPDC","REAL OBSERVED","Latest Maitri + Bharati station observations are pulled from the public NCPOR/NPDC station pages in REAL mode."),
("⛅","IMD Polar WRF","REAL FORECAST","Official Polar WRF forecast stream is kept separate from observations; the adapter accepts official CSV/JSON exports."),
("⚙","Operational telemetry","SIMULATED","Equipment, energy, inventory and logistics use synthetic data because internal station telemetry is not public."),
("✦","AI / ML layer","PREDICTION","Anomaly, energy forecast, risk and recommendations are model outputs and always labelled as decision support."),]
for c,(icon,title,badge,copy) in zip((s1,s2,s3,s4),source_cards):
    with c: st.markdown(f'<div class="source-card"><div class="source-icon">{icon}</div><div class="source-title">{title}</div><div style="margin:7px 0">{provenance_badge("REAL_OBSERVED" if "NCPOR" in title else "REAL_FORECAST" if "IMD" in title else "SIMULATED_DEMO" if "Operational" in title else "MODEL_PREDICTION")}</div><div class="source-copy">{copy}</div></div>',unsafe_allow_html=True)

# IMPACT
st.markdown("### 🚀 Why it matters")
imp1,imp2,imp3,imp4=st.columns(4)
for c,big,small in [(imp1,"Monitor → Predict → Prevent","Replace reactive operations with proactive decision support"),(imp2,"Safety first","Detect weather, equipment and resource risks earlier"),(imp3,"Energy + logistics","Forecast demand and plan supplies before constraints become critical"),(imp4,"Offline ready","Keep the twin useful when Antarctic connectivity is unstable")]:
    with c: st.markdown(f'<div class="impact"><div class="impact-big">{big}</div><div class="impact-small">{small}</div></div>',unsafe_allow_html=True)

st.caption("POLAR TWIN SENTINEL • Decision-support prototype • Human approval required • Not an official Government of India / NCPOR system")
