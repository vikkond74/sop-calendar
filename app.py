import streamlit as st
import pandas as pd
import holidays
from datetime import date, timedelta
from ics import Calendar, Event

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="S&OP Calendar Prototype", layout="wide")
st.title("📅 S&OP Calendar & Logic Manager")

# 1. Define Holidays for LUX, BEL, USA
years = [2025, 2026]
all_holidays = {
    "Luxembourg": holidays.LU(years=years),
    "Belgium": holidays.BE(years=years),
    "USA": holidays.US(years=years)
}

# 2. Sidebar - Logic Upload & Lock
with st.sidebar:
    st.header("Admin Controls")
    is_locked = st.toggle("Lock Events (Admin Only)", value=False)
    password = st.text_input("Admin Password", type="password") if is_locked else None
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Workday Logic (Excel)", type=['xlsx'])

# 3. Workday Calculation Logic
def get_nth_workday(year, month, nth_day, holiday_list):
    """Calculates the Nth workday of a month skipping weekends and holidays."""
    count = 0
    current_date = date(year, month, 1)
    
    while count < nth_day:
        # Check if weekend or holiday
        is_weekend = current_date.weekday() >= 5
        is_holiday = current_date in holiday_list
        
        if not is_weekend and not is_holiday:
            count += 1
        
        if count < nth_day:
            current_date += timedelta(days=1)
            
    return current_date

# 4. Main Calendar View
tab1, tab2 = st.tabs(["Calendar View", "Logic Configuration"])

with tab2:
    st.subheader("Current Workday Logic")
    if uploaded_file:
        df_logic = pd.read_excel(uploaded_file)
        st.dataframe(df_logic, use_container_width=True)
    else:
        st.info("Please upload an Excel file with 'Event Name' and 'Workday' columns.")

with tab1:
    col1, col2 = st.columns([1, 3])
    with col1:
        target_month = st.selectbox("Select Month", range(1, 13), index=date.today().month - 1)
        target_year = st.selectbox("Select Year", years, index=1)
        
    st.subheader(f"Schedule for {date(target_year, target_month, 1).strftime('%B %Y')}")
    
    # Display Holidays
    st.write("### 🌍 Regional Holidays")
    h_cols = st.columns(3)
    colors = {"Luxembourg": "blue", "Belgium": "red", "USA": "green"}
    
    for i, (country, h_list) in enumerate(all_holidays.items()):
        country_hols = [f"{d}: {name}" for d, name in h_list.items() if d.month == target_month and d.year == target_year]
        with h_cols[i]:
            st.markdown(f":{colors[country]}[**{country}**]")
            for h in country_hols:
                st.caption(h)

    # 5. Export to Outlook (.ics)
    if st.button("📤 Export to Outlook"):
        c = Calendar()
        # (Logic to add events to 'c' goes here)
        st.download_button("Download .ics File", str(c), file_name="sop_schedule.ics")
