import streamlit as st
import config
import re
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, provenance_badge
from src.ai.copilot import ask as ask_real_ai, is_configured as real_ai_configured

st.set_page_config(page_title="AI Copilot — Polar Twin Sentinel", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
inject_base_css(); ensure_db()
scenario=get_current_scenario(); mode=get_current_data_mode()
try: result=get_pipeline_result(scenario,mode)
except RuntimeError as exc: st.error(str(exc)); st.stop()
stations=result["stations"]
y
st.markdown('<div class="pts-hero"><div class="pts-kicker">DECISION SUPPORT • GROUNDED AI</div><div class="pts-title">AI OPERATIONS COPILOT</div><div class="pts-sub">Ask the Digital Twin questions in plain language. Answers are grounded in the current pipeline and never pretend simulated telemetry is real.</div></div>', unsafe_allow_html=True)

def answer(q):
    q=(q or '').lower().strip()
    if not q: return 'Type a question or choose a command below.'
    if any(k in q for k in ['higher risk','worst risk','highest risk','risk first']):
        sid=max(stations,key=lambda x:stations[x]['overall_risk']['score']); s=stations[sid]; dom=max(s['sub_risks'],key=lambda k:s['sub_risks'][k]['score'])
        return f"**{sid}** needs attention first: **{s['overall_risk']['score']}/100 ({s['overall_risk']['level']})**. Largest domain: **{dom}**."
    if any(k in q for k in ['condition','status','current weather']):
        return '\n\n'.join([f"**{sid}** — {s['weather_df'].iloc[-1]['temperature_c']:.1f}°C, {s['weather_df'].iloc[-1]['humidity_pct']:.0f}% RH, {s['weather_df'].iloc[-1]['pressure_hpa']:.1f} hPa, {s['weather_df'].iloc[-1]['wind_speed_kmh']:.1f} km/h; risk {s['overall_risk']['score']}/100." for sid,s in stations.items()])
    if any(k in q for k in ['ncp','real data','observation']):
        return '\n\n'.join([f"**{sid}:** {s['weather_df'].iloc[-1]['source']} → **{s['weather_df'].iloc[-1]['data_status']}**." for sid,s in stations.items()])
    if any(k in q for k in ['imd','forecast']):
        return '\n\n'.join([f"**{sid}:** {len(s.get('imd_forecast_df',[]))} official IMD Polar WRF rows loaded." if not s.get('imd_forecast_df',None) is None and not s.get('imd_forecast_df').empty else f"**{sid}:** IMD Polar WRF adapter ready; no official export loaded, so forecast values are not invented." for sid,s in stations.items()])
    if any(k in q for k in ['equipment','maintenance','machine']):
        rows=[(r['anomaly_probability'],sid,r) for sid,s in stations.items() for r in s['anomaly_results']]
        if not rows: return 'Equipment telemetry is unavailable. The prototype uses synthetic operational history because internal station telemetry is not public.'
        _,sid,r=max(rows,key=lambda x:x[0]); return f"**{r['equipment_id']} at {sid}** has the strongest anomaly signal: health **{r['health_pct']}%**, anomaly probability **{r['anomaly_probability']}**, priority **{r['priority']}**."
    if any(k in q for k in ['energy','power','fuel']):
        return '\n\n'.join([f"**{sid}:** {s['energy_df'].iloc[-1]['consumption_kw']:.0f} kW consumption, {s['energy_df'].iloc[-1]['generator_load_pct']:.0f}% load, {s['energy_df'].iloc[-1]['fuel_level_pct']:.1f}% fuel. [SIMULATED_DEMO]" for sid,s in stations.items()])
    if any(k in q for k in ['inventory','resource','supply','logistics']):
        out=[]
        for sid,s in stations.items():
            inv=s['inventory_df'].copy(); inv['days_left']=inv['quantity']/inv['daily_usage'].replace(0,float('nan')); row=inv.sort_values('days_left').iloc[0]; out.append(f"**{sid}:** {row['item_name']} has about **{row['days_left']:.0f} days** remaining vs **{row['lead_time_days']:.0f} days** lead time.")
        return '\n\n'.join(out)
    if any(k in q for k in ['what if','simulation','scenario']): return 'Open **What-If Mission Lab** and change temperature, wind, pressure, equipment stress, energy demand or logistics delay. The projected risk updates immediately.'
    if any(k in q for k in ['offline','connectivity']): return 'The platform is offline-first: latest NCPOR observations can be cached locally, while synthetic operational telemetry remains available during network loss. Freshness is shown explicitly.'
    if any(k in q for k in ['recommend','action','should','review']): return '\n\n'.join([f"**{sid}:** {s['recommendations'][0]['title'] if s['recommendations'] else 'Continue routine monitoring.'} — human approval required." for sid,s in stations.items()])
    return 'I can answer about **NCPOR observations, IMD forecast status, station condition, risk, equipment, energy, inventory, logistics, what-if simulation and offline readiness**.'

qs=['Which station needs attention first?','What is the current station condition?','What does NCPOR provide?','What is the IMD forecast status?','Which equipment needs attention?','What resources are critical?','What should the team review?','What if wind increases by 50 km/h?','Will it work offline?']
left,right=st.columns([.9,1.5],gap='large')
with left:
    st.markdown('<div class="panel"><div class="panel-title">QUICK COMMANDS</div>',unsafe_allow_html=True)
    for i,q in enumerate(qs):
        if st.button(q,use_container_width=True,key=f'qi_{i}'): st.session_state['ai_question']=q
    st.markdown('</div>',unsafe_allow_html=True)
with right:
    st.markdown('<div class="ai-box"><div class="panel-title">ASK THE DIGITAL TWIN</div>',unsafe_allow_html=True)
    with st.form("ai_form", clear_on_submit=False):
        q=st.text_input('Your question',value=st.session_state.get('ai_question',''),placeholder='e.g. What is the biggest risk at Bharati?')
        submitted=st.form_submit_button('✦ ASK AI',use_container_width=True)
    if submitted:
        real = ask_real_ai(q, result)
        st.session_state['ai_answer'] = real['text'] if real['mode'] in ('OPENAI_AGENT','OPENAI_ERROR') else answer(q)
        st.session_state['ai_mode'] = real['mode']
        st.session_state['ai_web'] = real.get('used_web', False)
        st.session_state['ai_question']=q
    if st.session_state.get('ai_answer'):
        mode_value = st.session_state.get('ai_mode')
        mode_label = 'OPENAI AI AGENT' if mode_value == 'OPENAI_AGENT' else ('OPENAI CONNECTION ERROR' if mode_value == 'OPENAI_ERROR' else 'LOCAL GROUNDED FALLBACK')
        web_label = ' • WEB SEARCH USED' if st.session_state.get('ai_web') else ''
        st.caption(f'Assistant: {mode_label}{web_label}')
        st.markdown(f'<div class="answer">{st.session_state["ai_answer"].replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    else: st.info('Choose a quick command, type a question, and press ASK AI.')
    st.markdown('</div>',unsafe_allow_html=True)

st.markdown('### Historical environmental data')
hist_cols = st.columns(2)
for c, sid in zip(hist_cols, stations):
    hdf = stations[sid].get("historical_df")
    max_df = stations[sid].get("maximum_snowfall")
    with c:
        if hdf is not None and not hdf.empty:
            snow_text = "No snowfall field in loaded export."
            if max_df is not None and not max_df.empty:
                row = max_df.iloc[0]
                snow_text = f"Maximum snowfall: {row['snowfall_mm']:.2f} mm on {row['timestamp']}"
            st.success(f"{sid}: {len(hdf)} historical rows loaded. {snow_text}")
        else:
            st.info(f"{sid}: no authorised historical export loaded; historical snowfall answers remain unavailable.")

st.markdown('### Data grounding')
if real_ai_configured():
    st.success('AI Agent connected: OpenAI Responses API')
else:
    st.info('AI Agent not connected. Add OPENAI_API_KEY to the project .env file and restart the app.')
cols=st.columns(4)
for c,(title,status) in zip(cols,[("NCPOR observation","REAL_OBSERVED"),("IMD Polar WRF","REAL_FORECAST"),("Equipment / energy","SIMULATED_DEMO"),("AI outputs","MODEL_PREDICTION")]):
    with c: st.markdown(f'<div class="source-card"><div class="source-title">{title}</div><div style="margin-top:8px">{provenance_badge(status)}</div></div>',unsafe_allow_html=True)
st.caption('Decision support only • no autonomous station control • human approval required.')
