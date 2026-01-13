import streamlit as st
import pandas as pd
import holidays
from datetime import date, timedelta
from ics import Calendar, Event

st.set_page_config(page_title="S&OP Calendar", layout="wide")

# --- 1. SETUP HOLIDAYS ---
years = [2025, 2026]
lu_hols = holidays.LU(years=years)
be_hols = holidays.BE(years=years)
us_hols = holidays.US(years=years)

# Combine LUX and BEL for the workday logic
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

# --- 2. WORKDAY CALCULATION ENGINE ---
def calculate_date(year, month, wd_number, hol_set):
    count = 0
    current_date = date(year, month, 1)
    
    while count < wd_number:
        # Weekday (0-4 is Mon-Fri), and not in our combined holiday set
        if current_date.weekday() < 5 and current_date not in hol_set:
            count += 1
        
        if count < wd_number:
            current_date += timedelta(days=1)
            # Safety break to prevent infinite loops if logic is huge
            if current_date.year > year and current_date.month > 1:
                break
    return current_date

# --- 3. SIDEBAR & INPUT ---
with st.sidebar:
    st.header("S&OP Settings")
    target_year = st.selectbox("Year", years, index=1)
    target_month = st.selectbox("Month", range(1, 13), index=date.today().month - 1)
    is_locked = st.toggle("🔒 Lock Events", value=False)
    
    st.divider()
    st.info("Logic: Skips Weekends + LUX/BEL Holidays")

# --- 4. DATA PROCESSING ---
# This matches the list you provided
sop_logic = {
    3: "Alignment 1", 4: "Finance close", 5: "Pre S&OP", 
    6: "Product review", 7: "Local touchpoint", 9: "ML",
    10: "SBU", 12: "Debrief", 14: "HUB", 15: "Supply signoff",
    16: "DSO", 17: "MOR", 19: "ISO", 20: "PBU MOR"
}

events_scheduled = []
for wd, name in sop_logic.items():
    event_date = calculate_date(target_year, target_month, wd, logic_holidays)
    events_scheduled.append({"Date": event_date, "Event": name, "Type": "S&OP"})

# --- 5. DISPLAY ---
t1, t2 = st.tabs(["Calendar List", "Holiday Reference"])

with t1:
    st.subheader(f"Schedule for {date(target_year, target_month, 1).strftime('%B %Y')}")
    
    df = pd.DataFrame(events_scheduled)
    # Highlight the rows
    st.table(df)

    # Export Button
    if st.button("Generate Outlook File (.ics)"):
        cal = Calendar()
        for _, row in df.iterrows():
            e = Event()
            e.name = row['Event']
            e.begin = row['Date']
            e.make_all_day()
            cal.events.add(e)
        
        st.download_button("Download ICS", str(cal), file_name="sop_schedule.ics")

with t2:
    st.write("### Holidays this month")
    cols = st.columns(3)
    for i, (name, h_set, color) in enumerate([("Luxembourg", lu_hols, "blue"), ("Belgium", be_hols, "red"), ("USA", us_hols, "green")]):
        with cols[i]:
            st.markdown(f":{color}[**{name}**]")
            for d, h_name in h_set.items():
                if d.month == target_month and d.year == target_year:
                    st.caption(f"{d}: {h_name}")
