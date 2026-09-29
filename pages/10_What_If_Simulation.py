import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import config
from src.utils.state import ensure_db, get_pipeline_result, get_current_scenario, get_current_data_mode
from src.utils.ui_helpers import inject_base_css, provenance_badge, render_sidebar

st.set_page_config(page_title="What-If Mission Lab — Polar Twin Sentinel", page_icon="◇", layout="wide", initial_sidebar_state="expanded")
inject_base_css(); render_sidebar(); ensure_db()
st.markdown('''<div class="pts-hero"><div class="pts-kicker">SIMULATION BEFORE ACTION</div><div class="pts-title">WHAT-IF MISSION LAB</div><div class="pts-sub">Stress the digital twin with weather, equipment and energy scenarios. Compare the projected outcome before a human operator approves any action.</div></div>''',unsafe_allow_html=True)
scenario=get_current_scenario(); mode=get_current_data_mode()
try: result=get_pipeline_result(scenario,mode)
except RuntimeError as exc: st.error(str(exc)); st.stop()
station=st.selectbox("Station",list(config.STATIONS.keys())); s=result["stations"][station]
base=s["overall_risk"]["score"]

c1,c2=st.columns(2)
with c1:
    st.markdown('<div class="panel"><div class="panel-title">WEATHER SHOCK</div>',unsafe_allow_html=True)
    temp=st.slider("Temperature change (°C)",-25,15,0)
    wind=st.slider("Wind increase (km/h)",0,120,0)
    pressure=st.slider("Pressure drop (hPa)",0,50,0)
    st.markdown('</div>',unsafe_allow_html=True)
with c2:
    st.markdown('<div class="panel"><div class="panel-title">OPERATIONS SHOCK</div>',unsafe_allow_html=True)
    equipment=st.slider("Equipment stress (%)",0,100,0)
    energy=st.slider("Energy demand increase (%)",0,100,0)
    logistics=st.slider("Logistics delay (%)",0,100,0)
    st.markdown('</div>',unsafe_allow_html=True)

projected=min(100,round(base+abs(temp)*1.0+wind*.22+pressure*.65+equipment*.20+energy*.12+logistics*.10))
delta=projected-base
level="LOW" if projected<25 else "MEDIUM" if projected<50 else "HIGH" if projected<75 else "CRITICAL"
q1,q2,q3=st.columns(3)
q1.metric("Current risk",f"{base}/100")
q2.metric("Projected risk",f"{projected}/100",f"{delta:+.0f}")
q3.metric("Projected state",level)

fig=go.Figure(go.Indicator(mode="gauge+number",value=projected,title={"text":"Projected operational risk","font":{"color":"#dff7ff"}},number={"font":{"color":"#fff"}},gauge={"axis":{"range":[0,100]},"bar":{"color":"#3ddcff"},"steps":[{"range":[0,25],"color":"#0d4a40"},{"range":[25,50],"color":"#55430c"},{"range":[50,75],"color":"#5a2c12"},{"range":[75,100],"color":"#571927"}]}))
fig.update_layout(height=310,paper_bgcolor="rgba(0,0,0,0)",font_color="#dff7ff",margin=dict(l=20,r=20,t=60,b=10))
st.plotly_chart(fig,use_container_width=True)

if level in ("HIGH","CRITICAL"):
    st.warning("Projected conditions cross the high-risk envelope. Recommended workflow: verify source data → inspect affected equipment → review logistics/energy margin → obtain human approval before action.")
elif level=="MEDIUM": st.info("Projected conditions are elevated. Increase monitoring and compare against the latest IMD forecast.")
else: st.success("Projected conditions remain within the current operating envelope.")

st.markdown("### Decision trace")
rows=[("NCPOR observation",s["weather_provenance"]),("IMD forecast",s.get("imd_provenance","No forecast export loaded")),("Equipment",provenance_badge("SIMULATED_DEMO")),("Energy",provenance_badge("SIMULATED_DEMO")),("Risk engine","Transparent weighted rule engine"),("Action","Human approval required")]
st.table(pd.DataFrame(rows,columns=["Layer","Status"]))
