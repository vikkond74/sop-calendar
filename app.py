import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
import holidays
from datetime import date, timedelta

st.set_page_config(page_title="S&OP Visual Calendar", layout="wide")

# --- 1. SETUP DATA & HOLIDAYS ---
years = [2025, 2026]
lu_hols = holidays.LU(years=years)
be_hols = holidays.BE(years=years)
us_hols = holidays.US(years=years)
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

# Workday Logic Function
def calculate_date(year, month, wd_number, hol_set):
    count, current_date = 0, date(year, month, 1)
    while count < wd_number:
        if current_date.weekday() < 5 and current_date not in hol_set:
            count += 1
        if count < wd_number:
            current_date += timedelta(days=1)
    return current_date

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Calendar Controls")
    sel_year = st.selectbox("Year", years, index=1)
    sel_month = st.selectbox("Month", range(1, 13), index=date.today().month - 1)
    is_locked = st.toggle("🔒 Admin Lock", value=True)
    st.caption("When locked, events cannot be dragged (Visual only).")

# --- 3. GENERATE EVENTS ---
sop_logic = {
    3: "Alignment 1", 4: "Finance close", 5: "Pre S&OP", 6: "Product review",
    7: "Local touchpoint", 9: "ML", 10: "SBU", 12: "Debrief", 14: "HUB",
    15: "Supply signoff", 16: "DSO", 17: "MOR", 19: "ISO", 20: "PBU MOR"
}

calendar_events = []

# Add S&OP Events (Blue)
for wd, name in sop_logic.items():
    evt_date = calculate_date(sel_year, sel_month, wd, logic_holidays)
    calendar_events.append({
        "title": f"📅 {name}",
        "start": evt_date.isoformat(),
        "color": "#1E88E5",  # Professional Blue
        "allDay": True
    })

# Add Holiday Events (Color-coded)
for country, h_list, color in [("LU", lu_hols, "#FF5252"), ("BE", be_hols, "#FFD740"), ("US", us_hols, "#4CAF50")]:
    for d, h_name in h_list.items():
        if d.month == sel_month and d.year == sel_year:
            calendar_events.append({
                "title": f"🚩 {country}: {h_name}",
                "start": d.isoformat(),
                "color": color,
                "allDay": True
            })

# --- 4. DISPLAY CALENDAR ---
calendar_options = {
    "initialDate": date(sel_year, sel_month, 1).isoformat(),
    "headerToolbar": {"left": "", "center": "title", "right": ""},
    "editable": not is_locked,  # Toggle drag-and-drop based on lock
    "selectable": True,
}

state = calendar(events=calendar_events, options=calendar_options, key="sop_calendar")

# Information Panel
st.markdown("---")
cols = st.columns(4)
cols[0].markdown("🔵 **S&OP Event**")
cols[1].markdown("🔴 **Luxembourg Holiday**")
cols[2].markdown("🟡 **Belgium Holiday**")
cols[3].markdown("🟢 **USA Holiday**")
