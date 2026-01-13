import streamlit as st
import pandas as pd
import holidays
from datetime import date, timedelta, datetime
from streamlit_calendar import calendar
from ics import Calendar, Event

st.set_page_config(page_title="S&OP Test Environment", layout="wide")

# --- 1. ENGINE ---
target_year = 2026
lu_hols = holidays.LU(years=[target_year])
be_hols = holidays.BE(years=[target_year])
us_hols = holidays.US(years=[target_year])
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

def get_sop_date(year, month, wd, hols):
    count, curr = 0, date(year, month, 1)
    wd = int(wd)
    while count < wd:
        # Skip Sat (5), Sun (6) and LUX/BEL Holidays
        if curr.weekday() < 5 and curr not in hols:
            count += 1
        if count < wd: 
            curr += timedelta(days=1)
    return curr

if 'master_data' not in st.session_state:
    st.session_state.master_data = pd.DataFrame()

# --- 2. TABS ---
tab1, tab2 = st.tabs(["📅 January Calendar", "⚙️ Setup"])

with tab2:
    st.header("Upload Logic")
    file = st.file_uploader("Upload Excel", type=['xlsx'])
    if file:
        st.session_state.master_data = pd.read_excel(file)
        st.success("Logic Loaded for January Test!")

with tab1:
    if st.session_state.master_data.empty:
        st.warning("Please upload your Excel logic in the Setup tab.")
    else:
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.write("### 📤 Export Test")
            if st.button("Extract Jan to Outlook"):
                c = Calendar()
                # Test logic: Only January
                for _, row in st.session_state.master_data.iterrows():
                    d = get_sop_date(target_year, 1, row['WD_Offset'], logic_holidays)
                    e = Event()
                    e.name = str(row['Event_Name'])
                    e.begin = datetime.combine(d, datetime.min.time())
                    e.make_all_day()
                    # No description/related fields added here
                    c.events.add(e)
                
                st.download_button(
                    label="Download Jan_SOP.ics",
                    data=str(c),
                    file_name="Jan_SOP_Test.ics",
                    mime="text/calendar"
                )
            
            st.divider()
            st.write("**Legend**")
            st.caption("🔵 S&OP Event")
            st.caption("🔴 Holiday")

        # --- CALENDAR DISPLAY (Fixed to Jan) ---
        cal_events = []
        
        # Add S&OP Events for Jan
        for _, row in st.session_state.master_data.iterrows():
            d = get_sop_date(target_year, 1, row['WD_Offset'], logic_holidays)
            cal_events.append({
                "title": str(row['Event_Name']),
                "start": d.isoformat(),
                "color": "#1E88E5",
                "allDay": True
            })
            
        # Add Holidays for Jan
        for country, h_list, color in [("LU", lu_hols, "#FF5252"), ("BE", be_hols, "#FFD740"), ("US", us_hols, "#4CAF50")]:
            for d, h_name in h_list.items():
                if d.month == 1:
                    cal_events.append({
                        "title": f"🚩 {country}: {h_name}",
                        "start": d.isoformat(),
                        "color": color,
                        "allDay": True
                    })

        calendar_options = {
            "initialDate": "2026-01-01",
            "initialView": "dayGridMonth",
            "headerToolbar": {"left": "", "center": "title", "right": ""},
        }
        
        calendar(events=cal_events, options=calendar_options, key="jan_test_cal")
