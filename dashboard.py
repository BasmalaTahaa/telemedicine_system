"""
🏥 TeleMedicine Live Dashboard — dashboard.py  (v2)
Run with:  streamlit run dashboard.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TeleMedicine Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
ACCENT     = "#4f8ef7"
BG_DARK    = "#0d1117"
BG_CARD    = "#161b22"
BG_CARD2   = "#1c2230"
BORDER     = "#30363d"
TEXT_MAIN  = "#e6edf3"
TEXT_MUTED = "#8b949e"

RISK_COLORS = {"Normal": "#2ecc71", "Warning": "#f0a500", "Critical": "#e74c3c"}
RISK_ICONS  = {"Normal": "🟢", "Warning": "🟡", "Critical": "🔴"}
RISK_BG     = {"Normal": "#2ecc7118", "Warning": "#f0a50018", "Critical": "#e74c3c25"}

CASE_COLORS = {
    "Cardiovascular":     "#e74c3c",
    "Diabetic":           "#3498db",
    "Respiratory":        "#2ecc71",
    "Fever/Infection":    "#f39c12",
    "General Monitoring": "#9b59b6",
}

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Base ──────────────────────────────────────────────────────── */
.stApp, .main {{ background-color: {BG_DARK}; color: {TEXT_MAIN}; }}
section[data-testid="stSidebar"] {{
    background-color: #0d1b2e;
    border-right: 1px solid {BORDER};
}}

/* ── Typography ─────────────────────────────────────────────────── */
h1,h2,h3,h4 {{ color: {TEXT_MAIN} !important; letter-spacing: 0.5px; }}

/* ── KPI Card ───────────────────────────────────────────────────── */
.kpi-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 18px 16px 14px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform .15s, box-shadow .15s;
}}
.kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,.5);
}}
.kpi-card::before {{
    content: '';
    position: absolute; top:0; left:0; right:0; height:3px;
    background: var(--kpi-accent, {ACCENT});
    border-radius: 14px 14px 0 0;
}}
.kpi-value {{ font-size: 2.2rem; font-weight: 800; margin: 0; line-height: 1.1; }}
.kpi-label {{
    font-size: 0.72rem; color: {TEXT_MUTED}; margin: 6px 0 0;
    text-transform: uppercase; letter-spacing: 1px;
}}
.kpi-delta {{ font-size: 0.72rem; margin-top: 4px; }}
.kpi-bar-wrap {{
    background: {BORDER}; border-radius: 4px; height: 4px; margin-top: 10px;
}}
.kpi-bar {{
    height: 4px; border-radius: 4px;
    background: var(--kpi-accent, {ACCENT});
    transition: width .4s;
}}

/* ── Section header ─────────────────────────────────────────────── */
.section-header {{
    font-size: 1rem; font-weight: 700; color: {TEXT_MAIN};
    border-left: 4px solid {ACCENT}; padding-left: 10px;
    margin-bottom: 12px; margin-top: 4px;
}}

/* ── Patient Card ───────────────────────────────────────────────── */
.pcard {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-left: 4px solid var(--card-color, #444);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: box-shadow .15s;
}}
.pcard:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,.4); }}
.pcard-critical {{
    background: linear-gradient(135deg, #1e0f0f, #2a1515);
}}
.pcard-title {{
    font-size: 1rem; font-weight: 700;
    display: flex; justify-content: space-between; align-items: center;
}}
.pcard-readings {{
    font-size: 0.78rem; color: {TEXT_MUTED}; margin-top: 6px; line-height: 1.8;
}}
.pcard-alert {{ font-size: 0.78rem; color: #e74c3c; margin-top: 3px; }}
.pcard-rec   {{ font-size: 0.76rem; color: #7ecfaa; margin-top: 2px; }}
.pcard-time  {{ font-size: 0.68rem; color: #555; margin-top: 3px; }}

/* ── Risk badge ─────────────────────────────────────────────────── */
.risk-badge {{
    border-radius: 20px; padding: 3px 12px;
    font-size: 0.72rem; font-weight: 700;
    border: 1px solid var(--badge-color);
    color: var(--badge-color);
    background: var(--badge-bg);
    white-space: nowrap;
}}

/* ── Alert strip ─────────────────────────────────────────────────── */
.alert-strip {{
    background: linear-gradient(90deg, #e74c3c22, #e74c3c0a);
    border: 1px solid #e74c3c55;
    border-left: 4px solid #e74c3c;
    border-radius: 8px;
    padding: 10px 16px;
    margin: 5px 0;
    animation: pulse 2s infinite;
}}
@keyframes pulse {{ 0%,100%{{ opacity:1 }} 50%{{ opacity:.75 }} }}

/* ── Tabs ───────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: {BG_CARD};
    border-radius: 10px 10px 0 0;
    border-bottom: 2px solid {BORDER};
    gap: 0;
}}
.stTabs [data-baseweb="tab"] {{
    color: {TEXT_MUTED}; padding: 10px 22px;
    font-weight: 600; font-size: 0.88rem;
}}
.stTabs [aria-selected="true"] {{
    color: {ACCENT} !important;
    border-bottom: 2px solid {ACCENT};
}}

/* ── Scrollbar ──────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {BG_DARK}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
DB_PATH = "telemedicine.db"

PARAMETER_RANGES = {
    "heart_rate":         (20,  220,  60,  100,  50,  120),
    "blood_pressure_sys": (50,  250,  90,  120,  80,  140),
    "blood_pressure_dia": (30,  150,  60,   80,  50,   90),
    "spo2":               (50,  100,  95,  100,  90,  100),
    "glucose_level":      (30,  600,  70,  140,  60,  200),
    "insulin_level":      (0,   300,   2,   25,   1,   50),
    "respiratory_rate":   (4,    60,  12,   20,  10,   25),
    "body_temperature":   (32,   43, 36.1, 37.2, 35,  38),
}
SENSOR_UNITS = {
    "heart_rate":         "BPM",
    "blood_pressure_sys": "mmHg",
    "blood_pressure_dia": "mmHg",
    "spo2":               "%",
    "glucose_level":      "mg/dL",
    "insulin_level":      "µU/mL",
    "respiratory_rate":   "br/min",
    "body_temperature":   "°C",
}
SENSOR_LABELS = {
    "heart_rate":         "Heart Rate",
    "blood_pressure_sys": "BP Systolic",
    "blood_pressure_dia": "BP Diastolic",
    "spo2":               "SpO₂",
    "glucose_level":      "Glucose",
    "insulin_level":      "Insulin",
    "respiratory_rate":   "Resp. Rate",
    "body_temperature":   "Body Temp",
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        readings = pd.read_sql_query(
            "SELECT * FROM readings ORDER BY id DESC LIMIT 5000", conn
        )
        risk_df = pd.read_sql_query(
            "SELECT * FROM patient_risk ORDER BY patient_id", conn
        )
        conn.close()
        return readings, risk_df
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:16px 0 8px;'>
        <div style='font-size:2.4rem;'>🏥</div>
        <div style='font-size:1.1rem; font-weight:800; color:{TEXT_MAIN}; letter-spacing:1px;'>
            TeleMedicine
        </div>
        <div style='font-size:0.75rem; color:{TEXT_MUTED};'>Patient Monitoring System</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:0.68rem; color:{TEXT_MUTED}; text-transform:uppercase; "
        f"letter-spacing:1px; margin-bottom:8px;'>⚙️ Controls</div>",
        unsafe_allow_html=True,
    )

    refresh_rate = st.slider("Refresh interval (sec)", 2, 30, 5)
    show_critical_only = st.checkbox("Show Critical Patients Only", value=False)
    selected_case = st.selectbox(
        "Filter by Disease Group",
        ["All", "Cardiovascular", "Diabetic", "Respiratory", "Fever/Infection", "General Monitoring"],
    )

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:0.68rem; color:{TEXT_MUTED}; text-transform:uppercase; "
        f"letter-spacing:1px; margin-bottom:8px;'>📊 System Status</div>",
        unsafe_allow_html=True,
    )

    now_str  = datetime.datetime.now().strftime("%H:%M:%S")
    date_str = datetime.datetime.now().strftime("%b %d, %Y")
    st.markdown(f"""
    <div style='background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px; padding:12px;'>
        <div style='font-size:0.75rem; color:{TEXT_MUTED};'>🕐 Last refreshed</div>
        <div style='font-size:0.95rem; font-weight:700; color:{TEXT_MAIN};'>{now_str}</div>
        <div style='font-size:0.7rem; color:{TEXT_MUTED};'>{date_str}</div>
        <div style='margin-top:8px; font-size:0.75rem; color:{TEXT_MUTED};'>💾 Database</div>
        <div style='font-size:0.75rem; color:{ACCENT}; font-family:monospace;'>{DB_PATH}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:0.73rem; color:{TEXT_MUTED}; line-height:1.6;'>
        Real-time IoT telemedicine platform monitoring 50 patients across 5 disease groups with 8 sensor types.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style='background: linear-gradient(135deg, #0d1b2e 0%, #162032 60%, #0d2040 100%);
            border: 1px solid {BORDER}; border-radius: 16px;
            padding: 28px 32px 22px; margin-bottom: 24px;'>
    <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;'>
        <div>
            <div style='font-size:0.68rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:2px;'>
                Real-Time IoT Platform
            </div>
            <h1 style='font-size:1.9rem; font-weight:900; margin:4px 0 6px; color:{TEXT_MAIN};'>
                🏥 TeleMedicine Monitoring System
            </h1>
            <div style='font-size:0.83rem; color:{TEXT_MUTED};'>
                50 Patients &nbsp;·&nbsp; 5 Disease Groups &nbsp;·&nbsp; 8 Sensor Types &nbsp;·&nbsp; Live IoT Data Stream
            </div>
        </div>
        <div style='text-align:right;'>
            <div style='background:#2ecc7122; border:1px solid #2ecc71; border-radius:20px;
                        padding:6px 16px; display:inline-flex; align-items:center; gap:6px;'>
                <span style='width:8px; height:8px; background:#2ecc71; border-radius:50%;
                              display:inline-block; animation:pulse 1.5s infinite;'></span>
                <span style='font-size:0.8rem; color:#2ecc71; font-weight:700;'>LIVE</span>
            </div>
            <div style='font-size:0.7rem; color:{TEXT_MUTED}; margin-top:6px;'>
                Auto-refresh every {"{refresh}"}s
            </div>
        </div>
    </div>
</div>
""".replace('"{refresh}"', str(refresh_rate)), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

readings, risk_df = load_data()

if risk_df.empty:
    st.error("⚠️ No data found. Please run the notebook first to generate data.")
    st.info("Run: `telemedicine_system.ipynb` → Execute all cells → Then reload this dashboard.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# COMPUTED METRICS
# ─────────────────────────────────────────────────────────────────────────────

total       = len(risk_df)
critical_n  = len(risk_df[risk_df["risk_level"] == "Critical"])
warning_n   = len(risk_df[risk_df["risk_level"] == "Warning"])
normal_n    = len(risk_df[risk_df["risk_level"] == "Normal"])
total_rec   = len(readings)
valid_rec   = len(readings[readings["is_valid"] == 1]) if total_rec > 0 else 0
invalid_rec = total_rec - valid_rec
valid_pct   = 100 * valid_rec / total_rec if total_rec > 0 else 0
crit_rate   = 100 * critical_n / total if total > 0 else 0
warn_rate   = 100 * warning_n  / total if total > 0 else 0

# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────

def kpi_card(value, label, color, bar_pct=None, delta_text=None):
    bar_html = ""
    if bar_pct is not None:
        bar_html = (
            f"<div class='kpi-bar-wrap'>"
            f"<div class='kpi-bar' style='width:{min(bar_pct, 100):.0f}%; background:{color};'></div>"
            f"</div>"
        )
    delta_html = (
        f"<div class='kpi-delta' style='color:{color};'>{delta_text}</div>"
        if delta_text else ""
    )
    return (
        f"<div class='kpi-card' style='--kpi-accent:{color};'>"
        f"<div class='kpi-value' style='color:{color};'>{value}</div>"
        f"<div class='kpi-label'>{label}</div>"
        f"{delta_html}{bar_html}"
        f"</div>"
    )

kpi_cols = st.columns(7)
kpi_specs = [
    (str(total),          "Total Patients",  ACCENT,     None,             "👥 enrolled"),
    (str(normal_n),       "Normal",          "#2ecc71",  normal_n/total*100, f"{normal_n/total*100:.0f}% healthy"),
    (str(warning_n),      "Warning",         "#f0a500",  warn_rate,        f"{warn_rate:.0f}% at risk"),
    (str(critical_n),     "Critical",        "#e74c3c",  crit_rate,        f"{crit_rate:.0f}% critical"),
    (f"{total_rec:,}",    "Total Records",   "#9b59b6",  None,             "IoT readings"),
    (f"{valid_pct:.1f}%", "Data Quality",    "#1abc9c",  valid_pct,        f"{valid_rec:,} valid"),
    (str(invalid_rec),    "Invalid Records", "#e67e22",
     (invalid_rec / total_rec * 100) if total_rec > 0 else 0,
     f"{invalid_rec/total_rec*100:.1f}% error" if total_rec > 0 else "—"),
]
for col, (val, label, color, bar, delta) in zip(kpi_cols, kpi_specs):
    with col:
        st.markdown(kpi_card(val, label, color, bar, delta), unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL ALERTS PANEL
# ─────────────────────────────────────────────────────────────────────────────

critical_patients = risk_df[risk_df["risk_level"] == "Critical"]
if len(critical_patients) > 0:
    st.markdown(f"""
    <div style='background:#e74c3c12; border:1px solid #e74c3c44;
                border-radius:12px; padding:16px 20px; margin-bottom:16px;'>
        <div style='font-size:1rem; font-weight:800; color:#e74c3c; margin-bottom:10px;'>
            🚨 CRITICAL ALERTS &nbsp;
            <span style='background:#e74c3c; color:white; border-radius:20px;
                         padding:2px 10px; font-size:0.72rem;'>{len(critical_patients)}</span>
        </div>
    """, unsafe_allow_html=True)
    for _, row in critical_patients.iterrows():
        rec_txt = str(row.get("recommendation", "") or "")
        rec_short = rec_txt[:120] + ("…" if len(rec_txt) > 120 else "")
        st.markdown(f"""
        <div class='alert-strip'>
            🔴 <b style='color:{TEXT_MAIN};'>{row["patient_id"]}</b>
            <span style='color:{TEXT_MUTED}; font-size:0.85rem;'> · {row["case_type"]}</span>
            &nbsp;—&nbsp; <span style='color:#f08080;'>{row["abnormalities"]}</span><br>
            <span style='color:#7ecfaa; font-size:0.8rem;'>💊 {rec_short}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_MUTED, family="Inter, sans-serif", size=12),
    margin=dict(t=24, b=16, l=12, r=12),
)


def apply_grid(fig):
    fig.update_xaxes(gridcolor="#1e2530", zerolinecolor="#1e2530")
    fig.update_yaxes(gridcolor="#1e2530", zerolinecolor="#1e2530")
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab_overview, tab_patients, tab_analytics, tab_data = st.tabs([
    "📊  Overview & Charts",
    "🧑‍⚕️  Patient Monitor",
    "📈  Advanced Analytics",
    "📋  Raw Data",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

with tab_overview:
    col_l, col_r = st.columns([1.1, 1])

    # ── LEFT: Gauges + Donut ───────────────────────────────────────────────
    with col_l:
        g1, g2, g3 = st.columns(3)

        def make_gauge(value, title, color, max_val=100, suffix="%"):
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                number={"suffix": suffix, "font": {"size": 24, "color": TEXT_MAIN}},
                title={"text": title, "font": {"size": 11, "color": TEXT_MUTED}},
                gauge={
                    "axis": {"range": [0, max_val], "tickcolor": TEXT_MUTED, "tickwidth": 1},
                    "bar":  {"color": color, "thickness": 0.28},
                    "bgcolor": BG_CARD2,
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, max_val * 0.5],  "color": "#1a2030"},
                        {"range": [max_val * 0.5, max_val * 0.8], "color": "#1e2535"},
                        {"range": [max_val * 0.8, max_val],       "color": "#22293a"},
                    ],
                    "threshold": {
                        "line":      {"color": color, "width": 2},
                        "thickness": 0.75,
                        "value":     value,
                    },
                },
            ))
            fig.update_layout(**PLOTLY_BASE, height=180)
            return fig

        with g1:
            st.plotly_chart(make_gauge(crit_rate, "Critical Rate", "#e74c3c"), use_container_width=True)
        with g2:
            st.plotly_chart(make_gauge(warn_rate, "Warning Rate", "#f0a500"), use_container_width=True)
        with g3:
            st.plotly_chart(make_gauge(valid_pct, "Data Quality", "#1abc9c"), use_container_width=True)

        st.markdown("<div class='section-header'>Risk Level Distribution</div>", unsafe_allow_html=True)
        risk_counts = risk_df["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["Risk Level", "Count"]
        fig_donut = px.pie(
            risk_counts, names="Risk Level", values="Count",
            color="Risk Level", color_discrete_map=RISK_COLORS,
            hole=0.55,
        )
        fig_donut.update_traces(
            textfont_size=13, textfont_color=TEXT_MAIN,
            marker=dict(line=dict(color=BG_DARK, width=3)),
        )
        fig_donut.update_layout(
            **PLOTLY_BASE, height=260,
            legend=dict(orientation="h", y=-0.06, font=dict(size=12)),
            annotations=[dict(
                text=f"<b>{total}</b><br>patients",
                showarrow=False,
                font=dict(size=15, color=TEXT_MAIN),
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # ── RIGHT: Stacked bar + horizontal bar ─────────────────────────────────
    with col_r:
        st.markdown("<div class='section-header'>Risk by Disease Group</div>", unsafe_allow_html=True)
        cross = risk_df.groupby(["case_type", "risk_level"]).size().reset_index(name="count")
        fig_cross = px.bar(
            cross, x="case_type", y="count", color="risk_level",
            color_discrete_map=RISK_COLORS, barmode="stack",
            text="count",
        )
        fig_cross.update_traces(textposition="inside", textfont_size=11, textfont_color="white")
        fig_cross.update_layout(
            **PLOTLY_BASE, height=270,
            xaxis_tickangle=-20, xaxis_title="", yaxis_title="Patients",
            legend=dict(orientation="h", y=-0.22, title=""),
        )
        apply_grid(fig_cross)
        st.plotly_chart(fig_cross, use_container_width=True)

        st.markdown("<div class='section-header'>Patients per Disease Group</div>", unsafe_allow_html=True)
        case_counts = risk_df["case_type"].value_counts().reset_index()
        case_counts.columns = ["Case Type", "Count"]
        fig_hbar = px.bar(
            case_counts, x="Count", y="Case Type", orientation="h",
            color="Case Type", color_discrete_map=CASE_COLORS,
            text="Count",
        )
        fig_hbar.update_traces(textposition="outside", textfont_size=12, textfont_color=TEXT_MAIN)
        fig_hbar.update_layout(
            **PLOTLY_BASE, height=260,
            showlegend=False, xaxis_title="", yaxis_title="",
            xaxis=dict(showgrid=False),
        )
        apply_grid(fig_hbar)
        st.plotly_chart(fig_hbar, use_container_width=True)

    # ── Sensor Trend ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>📡 Live Sensor Trend</div>", unsafe_allow_html=True)

    if not readings.empty:
        sel_col1, sel_col2 = st.columns([2, 1])
        with sel_col1:
            selected_sensor = st.selectbox(
                "Select Sensor",
                options=list(SENSOR_UNITS.keys()),
                format_func=lambda k: f"{SENSOR_LABELS[k]} ({SENSOR_UNITS[k]})",
                key="trend_sensor",
            )
        with sel_col2:
            n_points = st.select_slider("Data points", [50, 100, 200, 500], value=200)

        trend_df = (
            readings[(readings["sensor_type"] == selected_sensor) & (readings["is_valid"] == 1)]
            .tail(n_points)
            .copy()
        )
        trend_df["timestamp"] = pd.to_datetime(trend_df["timestamp"])
        trend_df = trend_df.sort_values("timestamp")

        if not trend_df.empty:
            r = PARAMETER_RANGES.get(selected_sensor, (None,) * 6)
            fig_trend = go.Figure()

            if r[4] and r[5]:
                fig_trend.add_hrect(
                    y0=r[4], y1=r[5],
                    fillcolor="rgba(240,165,0,0.06)",
                    line_color="rgba(240,165,0,0.25)",
                    annotation_text="Warning threshold",
                    annotation_position="top right",
                    annotation_font_color="#f0a500",
                )
            if r[2] and r[3]:
                fig_trend.add_hrect(
                    y0=r[2], y1=r[3],
                    fillcolor="rgba(46,204,113,0.07)",
                    line_color="rgba(46,204,113,0.3)",
                    annotation_text="Normal range",
                    annotation_position="top left",
                    annotation_font_color="#2ecc71",
                )

            for case_type in sorted(trend_df["case_type"].unique()):
                sub   = trend_df[trend_df["case_type"] == case_type]
                color = CASE_COLORS.get(case_type, ACCENT)
                fig_trend.add_trace(go.Scatter(
                    x=sub["timestamp"], y=sub["value"],
                    mode="lines+markers",
                    name=case_type,
                    line=dict(width=1.5, color=color),
                    marker=dict(size=3, color=color),
                    opacity=0.85,
                    hovertemplate=(
                        f"<b>{case_type}</b><br>"
                        "Time: %{x|%H:%M:%S}<br>"
                        f"Value: %{{y:.1f}} {SENSOR_UNITS.get(selected_sensor, '')}"
                        "<extra></extra>"
                    ),
                ))

            fig_trend.update_layout(
                **PLOTLY_BASE,
                height=340,
                xaxis_title="Time",
                yaxis_title=f"{SENSOR_LABELS.get(selected_sensor, 'Value')} ({SENSOR_UNITS.get(selected_sensor, '')})",
                legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
                hovermode="x unified",
            )
            apply_grid(fig_trend)
            st.plotly_chart(fig_trend, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PATIENT MONITOR
# ══════════════════════════════════════════════════════════════════════════════

with tab_patients:
    filt = risk_df.copy()
    if show_critical_only:
        filt = filt[filt["risk_level"] == "Critical"]
    if selected_case != "All":
        filt = filt[filt["case_type"] == selected_case]

    n_crit_f = len(filt[filt["risk_level"] == "Critical"])
    n_warn_f = len(filt[filt["risk_level"] == "Warning"])
    n_norm_f = len(filt[filt["risk_level"] == "Normal"])

    st.markdown(f"""
    <div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; align-items:center;'>
        <span style='font-size:0.9rem; color:{TEXT_MUTED};'>
            Showing <b style='color:{TEXT_MAIN}'>{len(filt)}</b> patients
        </span>
        <span style='background:#e74c3c22; border:1px solid #e74c3c44; border-radius:20px;
                     padding:3px 12px; font-size:0.76rem; color:#e74c3c;'>🔴 {n_crit_f} Critical</span>
        <span style='background:#f0a50022; border:1px solid #f0a50044; border-radius:20px;
                     padding:3px 12px; font-size:0.76rem; color:#f0a500;'>🟡 {n_warn_f} Warning</span>
        <span style='background:#2ecc7122; border:1px solid #2ecc7144; border-radius:20px;
                     padding:3px 12px; font-size:0.76rem; color:#2ecc71;'>🟢 {n_norm_f} Normal</span>
    </div>
    """, unsafe_allow_html=True)

    # Summary table
    tbl = filt[["patient_id", "case_type", "risk_level"]].copy()
    tbl["Risk"] = tbl["risk_level"].map(RISK_ICONS).fillna("⚪") + " " + tbl["risk_level"]
    tbl = tbl.rename(columns={"patient_id": "Patient ID", "case_type": "Disease Group"})
    st.dataframe(
        tbl[["Patient ID", "Disease Group", "Risk"]],
        use_container_width=True,
        height=180,
        hide_index=True,
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>Patient Detail Cards</div>", unsafe_allow_html=True)

    # Build latest readings pivot
    if not readings.empty:
        latest_readings = (
            readings[readings["is_valid"] == 1]
            .sort_values("timestamp", ascending=False)
            .drop_duplicates(subset=["patient_id", "sensor_type"])
            .groupby(["patient_id", "sensor_type"])["value"]
            .first()
            .unstack(fill_value=None)
            .reset_index()
        )
    else:
        latest_readings = pd.DataFrame()

    # Cards in 2 columns
    filt_rows = list(filt.iterrows())
    for i in range(0, len(filt_rows), 2):
        pair = filt_rows[i : i + 2]
        card_cols = st.columns(2)
        for ci, (_, row) in enumerate(pair):
            risk    = row["risk_level"]
            color   = RISK_COLORS.get(risk, "#444")
            icon    = RISK_ICONS.get(risk, "⚪")
            extra   = "pcard-critical" if risk == "Critical" else ""

            readings_html = "<i style='color:#555;'>No readings yet</i>"
            if (
                not latest_readings.empty
                and row["patient_id"] in latest_readings["patient_id"].values
            ):
                pat_row = latest_readings[
                    latest_readings["patient_id"] == row["patient_id"]
                ].iloc[0]
                vals = []
                for s in SENSOR_UNITS:
                    if s in pat_row and pd.notna(pat_row[s]):
                        lbl  = SENSOR_LABELS.get(s, s)
                        unit = SENSOR_UNITS[s]
                        vals.append(
                            f"<b style='color:{TEXT_MAIN};'>{lbl}:</b> "
                            f"{pat_row[s]:.1f} "
                            f"<span style='color:{TEXT_MUTED};'>{unit}</span>"
                        )
                if vals:
                    readings_html = " &nbsp;&nbsp; ".join(vals)

            abnorm    = str(row.get("abnormalities", "") or "None")
            rec       = str(row.get("recommendation", "") or "")
            updated   = str(row.get("last_updated", "") or "")[:19]
            rec_short = rec[:110] + ("…" if len(rec) > 110 else "")

            # Pre-build fragments to avoid nested quotes inside f-string
            alert_html = (
                "<div class='pcard-alert'>⚠️ " + abnorm + "</div>"
                if abnorm != "None" else ""
            )
            badge_bg  = RISK_BG.get(risk, "#44444415")
            pid       = row["patient_id"]
            case_type = row["case_type"]

            card_html = (
                "<div class='pcard " + extra + "' style='--card-color:" + color + ";'>"
                "<div class='pcard-title'>"
                "<span>" + icon + " <b>" + pid + "</b>"
                "<span style='color:" + TEXT_MUTED + "; font-size:0.8rem; font-weight:400;'>"
                "&nbsp;" + case_type + "</span></span>"
                "<span class='risk-badge' style='--badge-color:" + color + "; --badge-bg:" + badge_bg + ";'>"
                + risk + "</span></div>"
                "<div class='pcard-readings'>" + readings_html + "</div>"
                + alert_html +
                "<div class='pcard-rec'>💊 " + rec_short + "</div>"
                "<div class='pcard-time'>🕒 " + updated + "</div>"
                "</div>"
            )

            with card_cols[ci]:
                st.markdown(card_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ADVANCED ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

with tab_analytics:
    if not readings.empty:
        al1, al2 = st.columns(2)

        # ── Sensor readings count ──────────────────────────────────────────
        with al1:
            st.markdown("<div class='section-header'>Readings Count per Sensor</div>", unsafe_allow_html=True)
            sensor_counts = (
                readings[readings["is_valid"] == 1]["sensor_type"]
                .value_counts()
                .reset_index()
            )
            sensor_counts.columns = ["Sensor", "Count"]
            sensor_counts["Label"] = sensor_counts["Sensor"].map(SENSOR_LABELS).fillna(sensor_counts["Sensor"])
            fig_sc = px.bar(
                sensor_counts, x="Label", y="Count",
                color="Count", color_continuous_scale="Blues",
                text="Count",
            )
            fig_sc.update_traces(textposition="outside", textfont_color=TEXT_MAIN)
            fig_sc.update_layout(
                **PLOTLY_BASE, height=280,
                coloraxis_showscale=False,
                xaxis_tickangle=-30, xaxis_title="", yaxis_title="Valid Readings",
            )
            apply_grid(fig_sc)
            st.plotly_chart(fig_sc, use_container_width=True)

        # ── Invalid records breakdown ──────────────────────────────────────
        with al2:
            st.markdown("<div class='section-header'>Invalid Records Breakdown</div>", unsafe_allow_html=True)
            inv_df = readings[readings["is_valid"] == 0]
            if len(inv_df) > 0:
                err_counts = inv_df["error_reason"].value_counts().reset_index()
                err_counts.columns = ["Reason", "Count"]
                fig_err = px.pie(
                    err_counts, names="Reason", values="Count",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.45,
                )
                fig_err.update_traces(
                    textfont_size=11,
                    marker=dict(line=dict(color=BG_DARK, width=2)),
                )
                fig_err.update_layout(
                    **PLOTLY_BASE, height=280,
                    legend=dict(orientation="h", y=-0.1, font=dict(size=10)),
                )
                st.plotly_chart(fig_err, use_container_width=True)
            else:
                st.success("✅ No invalid records detected.")

        # ── Heatmap ────────────────────────────────────────────────────────
        st.markdown(
            "<div class='section-header'>Average Sensor Value by Disease Group (Normalized)</div>",
            unsafe_allow_html=True,
        )
        valid_r = readings[readings["is_valid"] == 1].copy()
        heatmap_df = valid_r.groupby(["case_type", "sensor_type"])["value"].mean().unstack(fill_value=0)
        heatmap_norm = heatmap_df.copy()
        for col in heatmap_norm.columns:
            col_min, col_max = heatmap_norm[col].min(), heatmap_norm[col].max()
            if col_max > col_min:
                heatmap_norm[col] = (heatmap_norm[col] - col_min) / (col_max - col_min)
        heatmap_norm.columns = [SENSOR_LABELS.get(c, c) for c in heatmap_norm.columns]
        fig_heat = px.imshow(
            heatmap_norm,
            color_continuous_scale="RdYlGn_r",
            aspect="auto",
            text_auto=".2f",
        )
        fig_heat.update_layout(
            **PLOTLY_BASE, height=240,
            xaxis_title="", yaxis_title="",
            coloraxis_colorbar=dict(thickness=12, len=0.8, tickfont=dict(size=9)),
        )
        fig_heat.update_xaxes(tickangle=-20)
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption(
            "Normalized per sensor column (0 = min across groups, 1 = max). "
            "Use to spot which disease groups show elevated or depressed readings relative to others."
        )

        # ── Box plots ──────────────────────────────────────────────────────
        st.markdown(
            "<div class='section-header'>Sensor Value Distribution by Disease Group</div>",
            unsafe_allow_html=True,
        )
        box_sensor = st.selectbox(
            "Select sensor for distribution analysis:",
            options=list(SENSOR_UNITS.keys()),
            format_func=lambda k: f"{SENSOR_LABELS[k]} ({SENSOR_UNITS[k]})",
            key="box_sensor",
        )
        box_df = valid_r[valid_r["sensor_type"] == box_sensor]
        if not box_df.empty:
            r = PARAMETER_RANGES.get(box_sensor, (None,) * 6)
            fig_box = px.box(
                box_df, x="case_type", y="value",
                color="case_type", color_discrete_map=CASE_COLORS,
                points="outliers",
            )
            if r[2] and r[3]:
                fig_box.add_hline(
                    y=r[2], line_dash="dot", line_color="#2ecc71",
                    annotation_text="Normal min", annotation_font_color="#2ecc71",
                )
                fig_box.add_hline(
                    y=r[3], line_dash="dot", line_color="#2ecc71",
                    annotation_text="Normal max", annotation_font_color="#2ecc71",
                )
            fig_box.update_layout(
                **PLOTLY_BASE, height=320,
                xaxis_title="", yaxis_title=f"{SENSOR_LABELS[box_sensor]} ({SENSOR_UNITS[box_sensor]})",
                showlegend=False, xaxis_tickangle=-20,
            )
            apply_grid(fig_box)
            st.plotly_chart(fig_box, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RAW DATA
# ══════════════════════════════════════════════════════════════════════════════

with tab_data:
    st.markdown("<div class='section-header'>Patient Risk Summary</div>", unsafe_allow_html=True)
    st.dataframe(
        risk_df.rename(columns={
            "patient_id":    "Patient ID",
            "case_type":     "Disease Group",
            "risk_level":    "Risk Level",
            "abnormalities": "Abnormalities",
            "recommendation":"Recommendation",
            "last_updated":  "Last Updated",
        }),
        use_container_width=True,
        height=250,
        hide_index=True,
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>Latest IoT Readings</div>", unsafe_allow_html=True)

    tf1, tf2 = st.columns(2)
    with tf1:
        tbl_sensor = st.selectbox(
            "Filter by sensor",
            ["All"] + list(SENSOR_UNITS.keys()),
            format_func=lambda k: "All" if k == "All" else SENSOR_LABELS.get(k, k),
            key="tbl_sensor",
        )
    with tf2:
        tbl_validity = st.selectbox(
            "Filter by validity",
            ["All", "Valid Only", "Invalid Only"],
            key="tbl_valid",
        )

    raw_show = readings.head(200).copy()
    if tbl_sensor != "All":
        raw_show = raw_show[raw_show["sensor_type"] == tbl_sensor]
    if tbl_validity == "Valid Only":
        raw_show = raw_show[raw_show["is_valid"] == 1]
    elif tbl_validity == "Invalid Only":
        raw_show = raw_show[raw_show["is_valid"] == 0]

    raw_show["Status"] = raw_show["is_valid"].map({1: "✅ Valid", 0: "❌ Invalid"})
    raw_show["Sensor"] = raw_show["sensor_type"].map(SENSOR_LABELS).fillna(raw_show["sensor_type"])

    st.dataframe(
        raw_show[["patient_id", "case_type", "Sensor", "timestamp", "value", "unit", "Status", "error_reason"]]
        .rename(columns={
            "patient_id":   "Patient ID",
            "case_type":    "Disease Group",
            "timestamp":    "Timestamp",
            "value":        "Value",
            "unit":         "Unit",
            "error_reason": "Error Reason",
        }),
        use_container_width=True,
        height=380,
        hide_index=True,
    )

    csv_bytes = raw_show.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Download as CSV",
        data=csv_bytes,
        file_name=f"telemedicine_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER + AUTO-REFRESH
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style='text-align:center; padding:24px; color:{TEXT_MUTED}; font-size:0.76rem;
            border-top:1px solid {BORDER}; margin-top:24px;'>
    🏥 TeleMedicine Monitoring System &nbsp;·&nbsp;
    Real-Time IoT Patient Analytics &nbsp;·&nbsp;
    Auto-refreshing every <b style='color:{TEXT_MAIN}'>{refresh_rate}s</b> &nbsp;·&nbsp;
    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)

time.sleep(refresh_rate)
st.rerun()
