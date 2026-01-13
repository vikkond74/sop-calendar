import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
import holidays
from datetime import date, timedelta

st.set_page_config(page_title="S&OP Annual Calendar", layout="wide")

# --- 1. SETUP HOLIDAYS (LUX & BEL for logic, USA for display) ---
years = [2025, 2026]
lu_hols = holidays.LU(years=years)
be_hols = holidays.BE(years=years)
us_hols = holidays.US(years=years)
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

# --- 2. THE ENGINE: CALCULATE FULL YEAR ---
@st.cache_data # This keeps the app fast by remembering the math
def generate_annual_events(year):
    sop_logic = {
        3: "Alignment 1", 4: "Finance close", 5: "Pre S&OP", 6: "Product review",
        7: "Local touchpoint", 9: "ML", 10: "SBU", 12: "Debrief", 14: "HUB",
        15: "Supply signoff", 16: "DSO", 17: "MOR", 19: "ISO", 20: "PBU MOR"
    }
    
    all_year_events = []
    
    for month in range(1, 13):
        # Calculate each S&OP event for this month
        for wd, name in sop_logic.items():
            count, current_date = 0, date(year, month, 1)
            while count < wd:
                # Rule: Skip Weekends + LUX/BEL Holidays
                if current_date.weekday() < 5 and current_date not in logic_holidays:
                    count += 1
                if count < wd:
                    current_date += timedelta(days=1)
            
            all_year_events.append({
                "title": f"📅 {name}",
                "start": current_date.isoformat(),
                "color": "#1E88E5",
                "allDay": True,
                "extendedProps": {"type": "S&OP", "month": month}
            })

        # Add Regional Holidays for this month
        for country, h_list, color in [("LU", lu_hols, "#FF5252"), ("BE", be_hols, "#FFD740"), ("US", us_hols, "#4CAF50")]:
            for d, h_name in h_list.items():
                if d.year == year and d.month == month:
                    all_year_events.append({
                        "title": f"🚩 {country}: {h_name}",
                        "start": d.isoformat(),
                        "color": color,
                        "allDay": True,
                        "extendedProps": {"type": "Holiday", "month": month}
                    })
    
    return all_year_events

# --- 3. UI & VIEW SELECTION ---
with st.sidebar:
    st.header("S&OP Planner")
    target_year = st.selectbox("Select Year", years, index=1)
    view_mode = st.radio("Display Mode", ["Monthly Grid", "Full Year List"])
    st.divider()
    if view_mode == "Monthly Grid":
        target_month = st.selectbox("Month Focus", range(1, 13), index=0)

# Generate the data
all_events = generate_annual_events(target_year)

if view_mode == "Monthly Grid":
    # Show the interactive calendar
    calendar_options = {
        "initialDate": date(target_year, target_month, 1).isoformat(),
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "initialView": "dayGridMonth",
    }
    calendar(events=all_events, options=calendar_options, key="sop_annual_cal")

else:
    # Show a scrollable list of the entire year
    st.subheader(f"Full S&OP Schedule - {target_year}")
    df_all = pd.DataFrame([
        {"Date": e["start"], "Event": e["title"]} 
        for e in all_events if "📅" in e["title"]
    ])
    st.dataframe(df_all.sort_values("Date"), use_container_width=True, height=600)
