"""
🏥 TeleMedicine Live Dashboard — dashboard.py
Run with:  streamlit run dashboard.py

This dashboard reads from the SQLite database produced by the notebook.
It refreshes automatically every 3 seconds to simulate real-time monitoring.
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import datetime
import random
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

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
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stApp { background-color: #0f1117; }

    .patient-card {
        background: linear-gradient(135deg, #1a1d2e, #252840);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 6px 0;
        border-left: 5px solid #444;
        font-family: monospace;
    }
    .card-normal   { border-left-color: #2ecc71; }
    .card-warning  { border-left-color: #f39c12; }
    .card-critical { border-left-color: #e74c3c; background: linear-gradient(135deg, #2d1a1a, #3d2020); }

    .metric-box {
        background: #1e2030;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        border: 1px solid #2a2d45;
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .metric-label { font-size: 0.85rem; color: #888; margin: 0; }

    .critical-alert {
        background: linear-gradient(90deg, #e74c3c33, #e74c3c11);
        border: 1px solid #e74c3c;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 5px 0;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }

    h1 { color: #e8ecf4 !important; }
    h2 { color: #b0b8d0 !important; }
    h3 { color: #8890a8 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — must match notebook definitions
# ─────────────────────────────────────────────────────────────────────────────
DB_PATH  = "telemedicine.db"
CSV_PATH = "telemedicine_data.csv"

PARAMETER_RANGES = {
    "heart_rate"         : (20,  220,  60,  100,  50,  120),
    "blood_pressure_sys" : (50,  250,  90,  120,  80,  140),
    "blood_pressure_dia" : (30,  150,  60,   80,  50,   90),
    "spo2"               : (50,  100,  95,  100,  90,  100),
    "glucose_level"      : (30,  600,  70,  140,  60,  200),
    "insulin_level"      : (0,   300,   2,   25,   1,   50),
    "respiratory_rate"   : (4,    60,  12,   20,  10,   25),
    "body_temperature"   : (32,   43, 36.1, 37.2, 35,  38),
}

SENSOR_UNITS = {
    "heart_rate"         : "BPM",
    "blood_pressure_sys" : "mmHg",
    "blood_pressure_dia" : "mmHg",
    "spo2"               : "%",
    "glucose_level"      : "mg/dL",
    "insulin_level"      : "µU/mL",
    "respiratory_rate"   : "br/min",
    "body_temperature"   : "°C",
}

RISK_COLORS = {"Normal": "#2ecc71", "Warning": "#f39c12", "Critical": "#e74c3c"}
RISK_ICONS  = {"Normal": "🟢", "Warning": "🟡", "Critical": "🔴"}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3)  # Refresh every 3 seconds
def load_data():
    """Load all data from SQLite."""
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
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.markdown("## 🏥 TeleMedicine\n### Control Panel")
st.sidebar.markdown("---")

refresh_rate = st.sidebar.slider("🔄 Refresh rate (sec)", 1, 10, 3)
show_critical_only = st.sidebar.checkbox("🔴 Show Critical Only", False)
selected_case = st.sidebar.selectbox(
    "🏷 Filter by Disease Group",
    ["All", "Cardiovascular", "Diabetic", "Respiratory", "Fever/Infection", "General Monitoring"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Last updated:** {datetime.datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**DB:** `{DB_PATH}`")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style='text-align:center; padding: 20px 0 10px 0;'>
    <h1 style='font-size:2.5rem; font-weight:800; letter-spacing:2px;'>
        🏥 TeleMedicine Monitoring System
    </h1>
    <p style='color:#666; font-size:1rem;'>
        Real-Time IoT Patient Monitoring · 50 Patients · 5 Disease Groups
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

readings, risk_df = load_data()

if risk_df.empty:
    st.error("⚠️ No data found. Please run the notebook first to generate data.")
    st.info("Run: `telemedicine_system.ipynb` → Execute all cells → Then reload this dashboard.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# TOP METRICS ROW
# ─────────────────────────────────────────────────────────────────────────────

total      = len(risk_df)
critical_n = len(risk_df[risk_df['risk_level'] == 'Critical'])
warning_n  = len(risk_df[risk_df['risk_level'] == 'Warning'])
normal_n   = len(risk_df[risk_df['risk_level'] == 'Normal'])
total_rec  = len(readings)
valid_rec  = len(readings[readings['is_valid'] == 1]) if len(readings) > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""
    <div class='metric-box'>
        <p class='metric-value' style='color:#4a90e2;'>{total}</p>
        <p class='metric-label'>Total Patients</p>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-box'>
        <p class='metric-value' style='color:#2ecc71;'>{normal_n}</p>
        <p class='metric-label'>🟢 Normal</p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-box'>
        <p class='metric-value' style='color:#f39c12;'>{warning_n}</p>
        <p class='metric-label'>🟡 Warning</p>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-box'>
        <p class='metric-value' style='color:#e74c3c;'>{critical_n}</p>
        <p class='metric-label'>🔴 Critical</p>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class='metric-box'>
        <p class='metric-value' style='color:#9b59b6;'>{total_rec:,}</p>
        <p class='metric-label'>Total Records</p>
    </div>""", unsafe_allow_html=True)

with col6:
    pct = f"{100*valid_rec/total_rec:.1f}%" if total_rec > 0 else "N/A"
    st.markdown(f"""
    <div class='metric-box'>
        <p class='metric-value' style='color:#1abc9c;'>{pct}</p>
        <p class='metric-label'>Valid Rate</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL ALERTS BANNER
# ─────────────────────────────────────────────────────────────────────────────

critical_patients = risk_df[risk_df['risk_level'] == 'Critical']
if len(critical_patients) > 0:
    st.markdown("### 🚨 CRITICAL ALERTS")
    for _, row in critical_patients.iterrows():
        st.markdown(f"""
        <div class='critical-alert'>
            🔴 <b>{row['patient_id']}</b> ({row['case_type']}) — 
            {row['abnormalities']}<br>
            <small>💊 {row['recommendation']}</small>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS ROW
# ─────────────────────────────────────────────────────────────────────────────

col_chart1, col_chart2, col_chart3 = st.columns([1, 1, 1])

with col_chart1:
    st.markdown("#### Risk Distribution")
    risk_counts = risk_df['risk_level'].value_counts().reset_index()
    risk_counts.columns = ['Risk Level', 'Count']
    fig_pie = px.pie(
        risk_counts, names='Risk Level', values='Count',
        color='Risk Level',
        color_discrete_map=RISK_COLORS,
        hole=0.5,
    )
    fig_pie.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ccc', margin=dict(t=10, b=10, l=10, r=10),
        height=280, legend=dict(orientation='h', y=-0.1)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.markdown("#### Patients per Disease Group")
    case_counts = risk_df['case_type'].value_counts().reset_index()
    case_counts.columns = ['Case Type', 'Count']
    fig_bar = px.bar(
        case_counts, x='Count', y='Case Type',
        orientation='h',
        color='Count', color_continuous_scale='Blues',
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ccc', margin=dict(t=10, b=10, l=10, r=10),
        height=280, showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart3:
    st.markdown("#### Risk by Disease Group")
    if not risk_df.empty:
        cross = risk_df.groupby(['case_type', 'risk_level']).size().reset_index(name='count')
        fig_cross = px.bar(
            cross, x='case_type', y='count', color='risk_level',
            color_discrete_map=RISK_COLORS,
            barmode='stack',
        )
        fig_cross.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ccc', margin=dict(t=10, b=10, l=10, r=10),
            height=280,
            xaxis_tickangle=-30,
            legend=dict(orientation='h', y=-0.25, title=''),
        )
        fig_cross.update_xaxes(title='')
        st.plotly_chart(fig_cross, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# PATIENT TABLE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### 🧑‍⚕️ Patient Monitor — All 50 Patients")

# Apply filters
filtered = risk_df.copy()
if show_critical_only:
    filtered = filtered[filtered['risk_level'] == 'Critical']
if selected_case != "All":
    filtered = filtered[filtered['case_type'] == selected_case]

st.markdown(f"Showing **{len(filtered)}** patients")

# Get latest readings per patient as a pivot
if not readings.empty:
    latest_readings = (
        readings[readings['is_valid'] == 1]
        .sort_values('timestamp', ascending=False)
        .drop_duplicates(subset=['patient_id', 'sensor_type'])
        .groupby(['patient_id', 'sensor_type'])['value']
        .first()
        .unstack(fill_value=None)
        .reset_index()
    )
else:
    latest_readings = pd.DataFrame()

# Render patient cards
for _, row in filtered.iterrows():
    risk    = row['risk_level']
    icon    = RISK_ICONS.get(risk, "⚪")
    css_cls = f"card-{risk.lower()}"

    # Get readings for this patient
    pat_readings = ""
    if not latest_readings.empty and row['patient_id'] in latest_readings['patient_id'].values:
        pat_row = latest_readings[latest_readings['patient_id'] == row['patient_id']].iloc[0]
        vals = []
        for col in latest_readings.columns:
            if col != 'patient_id' and pd.notna(pat_row.get(col)):
                unit = SENSOR_UNITS.get(col, '')
                short = col.replace('blood_pressure_', 'BP_').replace('_', ' ')
                vals.append(f"<b>{short}</b>: {pat_row[col]:.1f} {unit}")
        pat_readings = " &nbsp;|&nbsp; ".join(vals)
    else:
        pat_readings = "<i>No readings yet</i>"

    abnorm = row.get('abnormalities', '') or 'None'
    rec    = row.get('recommendation', '') or ''
    updated = row.get('last_updated', '')[:19] if row.get('last_updated') else ''

    st.markdown(f"""
    <div class='patient-card {css_cls}'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <span style='font-size:1.05rem; font-weight:700;'>
                {icon} {row['patient_id']} &nbsp; <span style='color:#888; font-size:0.85rem;'>{row['case_type']}</span>
            </span>
            <span style='background:{RISK_COLORS.get(risk,"#444")}22;
                         border:1px solid {RISK_COLORS.get(risk,"#444")};
                         border-radius:20px; padding:2px 10px;
                         font-size:0.8rem; color:{RISK_COLORS.get(risk,"white")};
                         font-weight:600;'>
                {risk}
            </span>
        </div>
        <div style='margin-top:6px; font-size:0.82rem; color:#aaa;'>{pat_readings}</div>
        <div style='margin-top:4px; font-size:0.78rem; color:#e74c3c;'>
            {'⚠️ ' + abnorm if abnorm != 'None' else ''}
        </div>
        <div style='margin-top:3px; font-size:0.78rem; color:#7ecfaa;'>💊 {rec[:100]}{'...' if len(rec)>100 else ''}</div>
        <div style='margin-top:2px; font-size:0.7rem; color:#555;'>🕒 {updated}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SENSOR TRENDS (last 50 readings per sensor)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 📈 Sensor Trend — Latest 200 Valid Readings")

if not readings.empty:
    selected_sensor = st.selectbox(
        "Select sensor to visualize:",
        options=list(SENSOR_UNITS.keys()),
        index=0
    )

    trend_df = (
        readings[(readings['sensor_type'] == selected_sensor) & (readings['is_valid'] == 1)]
        .tail(200)
        .copy()
    )
    trend_df['timestamp'] = pd.to_datetime(trend_df['timestamp'])
    trend_df = trend_df.sort_values('timestamp')

    if not trend_df.empty:
        r = PARAMETER_RANGES.get(selected_sensor, (None,)*6)
        fig_trend = go.Figure()

        # Normal range band
        if r[2] and r[3]:
            fig_trend.add_hrect(
                y0=r[2], y1=r[3],
                fillcolor='rgba(46,204,113,0.08)',
                line_color='rgba(46,204,113,0.3)',
                annotation_text="Normal range",
                annotation_position="top left",
            )

        # Scatter per case type with different colors
        for case_type in trend_df['case_type'].unique():
            sub = trend_df[trend_df['case_type'] == case_type]
            fig_trend.add_trace(go.Scatter(
                x=sub['timestamp'], y=sub['value'],
                mode='markers+lines',
                name=case_type,
                marker=dict(size=4),
                line=dict(width=1),
                opacity=0.8,
            ))

        fig_trend.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ccc',
            height=350,
            xaxis_title="Time",
            yaxis_title=f"{selected_sensor.replace('_',' ').title()} ({SENSOR_UNITS.get(selected_sensor,'')})",
            legend=dict(orientation='h', y=-0.15),
            margin=dict(t=20, b=30),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# RAW DATA TABLE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
with st.expander("📋 View Raw IoT Records (latest 100)", expanded=False):
    if not readings.empty:
        show_df = readings.head(100).copy()
        show_df['Status'] = show_df['is_valid'].map({1: '✅ Valid', 0: '❌ Invalid'})
        st.dataframe(
            show_df[['patient_id','case_type','sensor_type','timestamp','value','unit','Status','error_reason']],
            use_container_width=True,
            height=350,
        )

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-REFRESH
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style='text-align:center; padding:20px; color:#444; font-size:0.8rem;'>
    Auto-refreshing every {refresh_rate} seconds · 
    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)

time.sleep(refresh_rate)
st.rerun()
