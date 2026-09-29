"""Shared visual system for Polar Twin Sentinel."""
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


def inject_base_css():
    st.markdown("""
    <style>
    :root{--navy:#031426;--navy2:#061d34;--panel:#09233d;--panel2:#0d2c49;--ice:#f4fbff;--muted:#91abc3;--cyan:#22d3ee;--blue:#38a7ff;--green:#25e0a4;--amber:#ffc857;--red:#ff718b}
    .stApp{background:radial-gradient(circle at 82% -5%,#163e67 0%,#071b31 35%,#03101f 78%);color:var(--ice)}
    [data-testid="stHeader"]{background:rgba(2,12,24,.72);backdrop-filter:blur(14px);height:3.4rem}
    [data-testid="stToolbar"]{display:flex}
    [data-testid="stSidebar"]{width:235px !important;background:linear-gradient(180deg,#061a31 0%,#031224 100%);border-right:1px solid #173a59}
    [data-testid="stSidebar"] > div:first-child{width:235px !important}
    [data-testid="stSidebar"] *{color:#dff2ff}
    [data-testid="stSidebarNav"]{display:none}
    [data-testid="stSidebarContent"]{padding-top:.55rem}
    .block-container{max-width:1280px;padding-top:.6rem;padding-bottom:2.5rem}
    h1,h2,h3{letter-spacing:-.025em;color:#f5fbff}
    .side-brand{display:flex;gap:11px;align-items:center;padding:14px 5px 18px;border-bottom:1px solid #183a57;margin-bottom:18px}
    .side-logo{width:45px;height:45px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.45rem;background:linear-gradient(145deg,#0c4b76,#0a2340);border:1px solid #24618d;box-shadow:0 8px 24px rgba(0,0,0,.25)}
    .side-title{font-size:1.02rem;font-weight:900;letter-spacing:.08em;color:#f4fbff}.side-subtitle{font-size:.84rem;font-weight:850;letter-spacing:.18em;color:#52ddff;margin-top:1px}.side-tag{font-size:.61rem;color:#789bb8;margin-top:4px}
    .side-section{font-size:.63rem;font-weight:850;letter-spacing:.15em;color:#6f98b9;margin:14px 3px 7px}
    .side-divider{height:1px;background:#173653;margin:17px 0 13px}
    .side-status{margin-top:12px;padding:10px 11px;border-radius:12px;border:1px solid #174866;background:rgba(8,31,52,.8);font-size:.72rem;color:#bfeaff;line-height:1.45}.side-status small{color:#7395b2;font-size:.62rem}.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#31e7ad;box-shadow:0 0 12px #31e7ad;margin-right:5px}
    [data-testid="stSidebar"] .stPageLink{border-radius:10px;margin:2px 0;padding:.34rem .55rem}.stPageLink:hover{background:rgba(44,132,196,.16)}
    [data-testid="stSidebar"] .stSelectbox label{font-size:.7rem;color:#789bb8}
    .pts-hero{position:relative;overflow:hidden;border:1px solid #245b82;border-radius:24px;padding:23px 28px 18px;margin-bottom:15px;min-height:165px;background:linear-gradient(90deg,rgba(4,19,35,.98) 0%,rgba(5,25,44,.92) 54%,rgba(6,32,53,.78) 100%);box-shadow:0 18px 55px rgba(0,0,0,.28)}
    .pts-hero:after{content:"";position:absolute;right:-5%;top:-25%;width:45%;height:260px;background:radial-gradient(circle,rgba(34,211,238,.18),transparent 67%);pointer-events:none}
    .hero-top{display:flex;justify-content:space-between;gap:30px;align-items:flex-start;position:relative;z-index:1}.hero-slogan{font-size:1rem;color:#e7f8ff;text-align:right;line-height:1.35;margin-top:7px;font-family:Georgia,serif;text-shadow:0 2px 14px #00101d}.hero-bottom{display:flex;align-items:center;gap:12px;margin-top:13px;position:relative;z-index:1}.hero-note{font-size:.68rem;color:#86a9c5}
    .pts-kicker{color:#58dcff;text-transform:uppercase;letter-spacing:.18em;font-size:.67rem;font-weight:900}.pts-title{font-size:2.28rem;font-weight:950;line-height:1.02;margin:6px 0;color:#f4fbff}.pts-title span{color:#42d8ff}.pts-sub{color:#b2cce1;max-width:850px;font-size:.92rem;line-height:1.48}.pts-live{display:inline-flex;gap:7px;align-items:center;padding:6px 11px;border-radius:999px;background:rgba(49,231,173,.11);border:1px solid rgba(49,231,173,.42);color:#76f4c5;font-size:.7rem;font-weight:850}.pts-dot{width:7px;height:7px;border-radius:50%;background:#31e7ad;box-shadow:0 0 14px #31e7ad}
    .status-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:7px 0 21px}.status-box{display:flex;gap:10px;align-items:center;border:1px solid #20547a;border-radius:15px;background:linear-gradient(145deg,rgba(9,32,54,.96),rgba(4,19,35,.96));padding:11px 13px;min-height:68px;box-shadow:0 8px 22px rgba(0,0,0,.14)}.status-icon{width:34px;height:34px;flex:0 0 34px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#54dcff;background:rgba(30,128,188,.15);border:1px solid #245a80;font-weight:900}.status-label{font-size:.56rem;color:#7ea2bf;text-transform:uppercase;letter-spacing:.12em}.status-value{font-size:.94rem;font-weight:900;color:#f4fbff;margin-top:3px}.status-sub{font-size:.62rem;color:#7797b2;margin-top:2px}
    .station-card{position:relative;border-radius:20px;overflow:hidden;border:1px solid #24618a;background:linear-gradient(180deg,#0b2b49,#061a2e);margin-bottom:7px;box-shadow:0 14px 40px rgba(0,0,0,.24)}
    .station-photo-wrap{position:relative;height:188px;overflow:hidden;background:#0a2138}.station-photo{display:block;width:100%;height:100%;object-fit:cover;object-position:center}.photo-shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(3,13,25,.03) 42%,rgba(3,14,26,.66) 100%)}.photo-live{position:absolute;right:13px;top:12px;padding:5px 10px;border-radius:999px;background:rgba(4,25,39,.78);border:1px solid rgba(49,231,173,.7);color:#74f3c3;font-size:.65rem;font-weight:900;backdrop-filter:blur(8px)}.photo-live i{display:inline-block;width:6px;height:6px;border-radius:50%;background:#31e7ad;margin-right:5px}
    .station-content{padding:12px 15px 15px}.station-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.station-name{font-size:1.16rem;font-weight:900;color:#f5fbff}.station-meta{color:#86a9c5;font-size:.71rem;margin-top:2px}.station-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:12px}.station-metric{background:rgba(3,17,31,.80);border:1px solid rgba(120,177,213,.16);border-radius:11px;padding:8px 9px}.station-metric label{display:block;color:#7598b5;font-size:.54rem;text-transform:uppercase;letter-spacing:.08em}.station-metric b{display:block;color:#f4fbff;font-size:.89rem;margin-top:4px}.station-metric span{display:block;color:#38d9ff;font-size:.55rem;margin-top:2px}
    .ops-strip{display:grid;grid-template-columns:1.05fr 1.45fr 1fr;gap:10px;margin:15px 0}.visual-panel{height:100%;min-height:225px;border:1px solid #1d4b6e;border-radius:16px;background:linear-gradient(145deg,rgba(8,31,53,.96),rgba(4,20,36,.98));padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.18)}.visual-title{font-size:.83rem;font-weight:850;color:#e8f7ff;margin-bottom:8px}.visual-title span{float:right;color:#46d9ff;font-size:.68rem}.map-box{position:relative;height:177px;border-radius:12px;background:radial-gradient(circle at 50% 40%,#183d5d 0%,#0b2944 58%,#06182c 100%);overflow:hidden;display:flex;align-items:center;justify-content:center}.map-ice{font-size:2.1rem;letter-spacing:.12em;color:#dff6ff;opacity:.55;transform:scaleX(1.15)}.map-pin{position:absolute;font-size:.68rem;font-weight:850;color:#e8fbff;background:rgba(4,18,33,.82);padding:4px 7px;border-radius:8px;border:1px solid #2a607f}.pin-maitri{left:32%;top:31%}.pin-bharati{right:28%;bottom:30%}.map-legend{display:flex;justify-content:space-between;font-size:.59rem;color:#7fa0ba;margin-top:6px}
    .alert-row{display:flex;gap:9px;align-items:center;border:1px solid rgba(93,147,181,.16);background:rgba(6,23,40,.72);border-radius:10px;padding:8px;margin-top:7px}.alert-icon{width:25px;height:25px;border-radius:8px;background:#11324c;display:flex;align-items:center;justify-content:center}.alert-row b{display:block;font-size:.68rem;color:#f3fbff}.alert-row small{display:block;color:#799ab4;font-size:.57rem;margin-top:2px}
    .stPlotlyChart{margin-top:-5px}.trend-title{min-height:auto;margin-bottom:0;padding-bottom:6px;border-bottom:0}.trend-title + div{margin-top:-10px;border:1px solid #1d4b6e;border-top:0;border-radius:0 0 16px 16px;background:linear-gradient(145deg,rgba(8,31,53,.96),rgba(4,20,36,.98));padding:0 7px 6px}
    .panel{background:linear-gradient(145deg,rgba(12,37,62,.94),rgba(6,23,40,.96));border:1px solid #1c4568;border-radius:17px;padding:17px;box-shadow:0 10px 35px rgba(0,0,0,.2);margin-bottom:14px}.panel-title{font-size:.74rem;color:#72dcff;text-transform:uppercase;letter-spacing:.13em;font-weight:850;margin-bottom:8px}.panel h3{margin:.1rem 0 .35rem;color:#effbff}
    .metric-card{background:rgba(8,28,49,.92);border:1px solid #1b3e60;border-radius:15px;padding:12px 14px;min-height:84px}.metric-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:#7e9db9}.metric-value{font-size:1.55rem;font-weight:850;color:#f3fbff;margin-top:4px}.chip{display:inline-flex;align-items:center;justify-content:center;padding:4px 8px;border-radius:8px;font-size:.59rem;font-weight:850;letter-spacing:.03em;margin-right:4px;white-space:nowrap}.chip-real{background:#063b33;color:#6ee7b7;border:1px solid #12624f}.chip-forecast{background:#10375a;color:#7dd3fc;border:1px solid #1c5a91}.chip-sim{background:#493506;color:#fcd34d;border:1px solid #76540c}.chip-ai{background:#2b2058;color:#c4b5fd;border:1px solid #513a91}
    .source-card{border:1px solid #1c4165;border-radius:15px;padding:13px;background:rgba(8,26,45,.86);height:100%;box-shadow:0 8px 24px rgba(0,0,0,.14)}.source-icon{font-size:1.25rem}.source-title{font-weight:800;color:white;margin-top:5px;font-size:.9rem}.source-copy{font-size:.76rem;color:#91abc3;line-height:1.4}.flow{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.flow-step{padding:9px 12px;border-radius:11px;border:1px solid #245076;background:#0b2038;color:#dff7ff;font-size:.78rem;font-weight:750}.flow-arrow{color:#3ddcff}.ai-box{border:1px solid #315a88;border-radius:18px;padding:18px;background:linear-gradient(120deg,rgba(17,46,78,.98),rgba(11,31,53,.98))}.answer{border-left:3px solid #3ddcff;background:rgba(61,220,255,.05);padding:13px 15px;border-radius:8px;color:#d9efff}.whatif{border:1px solid #315a88;border-radius:18px;padding:18px;background:linear-gradient(145deg,rgba(22,45,72,.95),rgba(10,27,48,.98))}.impact{border-radius:17px;border:1px solid #1d4569;padding:16px;background:linear-gradient(90deg,#09213a,#0d2b48)}.impact-big{font-size:1.55rem;font-weight:900;color:white}.impact-small{font-size:.72rem;color:#89a9c4}.stButton>button{border-radius:10px;border:1px solid #2a5b86;background:linear-gradient(135deg,#0d3557,#0d2742);color:#e8f8ff;font-weight:750}.stButton>button:hover{border-color:#3ddcff;color:white}div[data-testid="stPopover"] button{border-radius:10px}.small-muted{font-size:.74rem;color:#829bb4}
    @media (max-width:1100px){.status-grid{grid-template-columns:repeat(2,1fr)}.ops-strip{grid-template-columns:1fr}.station-metrics{grid-template-columns:repeat(2,1fr)}.pts-title{font-size:2rem}.hero-slogan{display:none}.block-container{max-width:96%}}
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    if "scenario" not in st.session_state:
        st.session_state.scenario = "NORMAL"

    with st.sidebar:
        st.markdown('''<div class="side-brand"><div class="side-logo">❄</div><div><div class="side-title">POLAR TWIN</div><div class="side-subtitle">SENTINEL</div><div class="side-tag">Monitor • Predict • Prevent</div></div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="side-section">MISSION CONTROL</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="⌂  Dashboard")
        st.page_link("pages/1_Station_Monitor.py", label="◈  Station Monitor")
        st.page_link("pages/2_Environment.py", label="◉  Environment")
        st.page_link("pages/3_Energy_Intelligence.py", label="⚡  Energy Intelligence")
        st.page_link("pages/4_Equipment_Health.py", label="⚙  Equipment Health")
        st.page_link("pages/5_Inventory_Logistics.py", label="▣  Inventory & Logistics")
        st.page_link("pages/6_Risk_Alerts.py", label="⚠  Risk & Alerts")
        st.page_link("pages/7_AI_Insights.py", label="✦  AI Insights")
        st.page_link("pages/8_Data_Explorer.py", label="⌁  Data Explorer")
        st.page_link("pages/9_Model_Performance.py", label="◫  Model Performance")
        st.page_link("pages/10_What_If_Simulation.py", label="◇  What-If Simulation")
        st.page_link("pages/11_System_Overview.py", label="◎  System Overview")
        st.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="side-section">SCENARIO LAB</div>', unsafe_allow_html=True)
        st.session_state.scenario = st.selectbox(
            "Scenario",
            config.DEMO_SCENARIOS,
            index=config.DEMO_SCENARIOS.index(st.session_state.scenario),
            label_visibility="collapsed",
        )
        if st.button("↻  Refresh live data", use_container_width=True):
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
        st.markdown('<div class="side-status"><span class="live-dot"></span><b>LATEST PUBLISHED</b><span> NCPOR</span><br><small>Published station observations • IMD forecast kept separate</small></div>', unsafe_allow_html=True)


def status_pill(label):
    color = config.COLORS.get(str(label).upper(), config.COLORS.get("INFO", "#3b82f6"))
    return f'<span class="polar-pill" style="background-color:{color};padding:4px 10px;border-radius:999px;font-size:.7rem;font-weight:800;color:#fff;">{label}</span>'


def provenance_badge(data_status):
    mapping={"REAL_OBSERVED":("chip-real","NCPOR • REAL OBSERVED"),"REAL_FORECAST":("chip-forecast","IMD • POLAR WRF FORECAST"),"REAL_REFERENCE":("chip-real","OFFICIAL REFERENCE"),"SIMULATED_DEMO":("chip-sim","SIMULATED • DEMO"),"SIMULATED_FALLBACK":("chip-sim","SIMULATED • FALLBACK"),"MODEL_PREDICTION":("chip-ai","AI • MODEL PREDICTION")}
    cls,text=mapping.get(data_status,("chip-sim",str(data_status)))
    return f'<span class="chip {cls}">{text}</span>'


def metric_card(label, value, pill_label=None, help_text=None):
    pill_html=status_pill(pill_label) if pill_label else ""
    help_html=f'<div class="small-muted">{help_text}</div>' if help_text else ""
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value} {pill_html}</div>{help_html}</div>',unsafe_allow_html=True)


def risk_factor_bars(factors, title="Contributing factors"):
    if not factors:
        st.caption("No contributing factors."); return
    names=[f.get("factor") or f.get("domain") for f in factors]
    vals=[f.get("contribution",f.get("score",0)) for f in factors]
    fig=go.Figure(go.Bar(x=vals,y=names,orientation="h",marker_color="#3ddcff",text=[f"{v:.0f}" for v in vals],textposition="outside"))
    fig.update_layout(title=title,height=max(180,40*len(names)),margin=dict(l=10,r=30,t=40,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#dff7ff",xaxis=dict(range=[0,105],gridcolor="#183750"),yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig,use_container_width=True)


def risk_gauge(score,title="Overall Operational Risk"):
    fig=go.Figure(go.Indicator(mode="gauge+number", value=score, title={"text": title, "font": {"color": "#dff7ff"}}, number={"font": {"color": "#fff"}}, gauge={"axis": {"range": [0,100], "tickcolor": "#8ea6bf"}, "bar": {"color": "#3ddcff"}, "steps": [{"range": [0,25], "color": "#0d4a40"}, {"range": [25,50], "color": "#55430c"}, {"range": [50,75], "color": "#5a2c12"}, {"range": [75,100], "color": "#571927"}]}))
    fig.update_layout(height=260,margin=dict(l=20,r=20,t=50,b=10),paper_bgcolor="rgba(0,0,0,0)",font_color="#dff7ff")
    st.plotly_chart(fig,use_container_width=True)


def simulated_data_banner():
    st.markdown('<div style="background:#4a3407;color:#fcd34d;padding:9px 13px;border-radius:9px;border:1px solid #76540c;font-size:.8rem;">⚠️ SIMULATED / DEMONSTRATION DATA — used only where public station telemetry is unavailable.</div>',unsafe_allow_html=True)
