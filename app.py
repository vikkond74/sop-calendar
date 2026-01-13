import streamlit as st
import pandas as pd
import holidays
from datetime import date, timedelta
from streamlit_calendar import calendar

# --- 1. INITIAL SETUP ---
st.set_page_config(page_title="S&OP Logic Manager", layout="wide")

# Pre-load holidays (skips weekends + LUX/BEL)
years = [2025, 2026]
lu_hols = holidays.LU(years=years)
be_hols = holidays.BE(years=years)
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

def get_sop_date(year, month, wd, hols):
    count, curr = 0, date(year, month, 1)
    while count < wd:
        if curr.weekday() < 5 and curr not in hols:
            count += 1
        if count < wd: curr += timedelta(days=1)
    return curr

# --- 2. DATA HANDLING ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = pd.DataFrame()

# --- 3. UI TABS ---
tab1, tab2, tab3 = st.tabs(["📅 S&OP Calendar", "📂 SAP Job Export", "⚙️ Upload Logic"])

with tab3:
    st.header("Step 1: Upload Your Logic")
    file = st.file_uploader("Upload Excel with WD_Offset, Event_Name, and Related_Scripts", type=['xlsx'])
    if file:
        st.session_state.master_data = pd.read_excel(file)
        st.success("Logic Loaded Successfully!")

with tab1:
    if st.session_state.master_data.empty:
        st.warning("Please upload logic in the Setup tab first.")
    else:
        col1, col2 = st.columns([1, 4])
        with col1:
            sel_month = st.selectbox("Month", range(1, 13), index=date.today().month - 1)
            is_locked = st.toggle("Admin Lock", value=True)
        
        # Build Calendar Events
        cal_events = []
        for _, row in st.session_state.master_data.iterrows():
            d = get_sop_date(2026, sel_month, row['WD_Offset'], logic_holidays)
            cal_events.append({
                "title": row['Event_Name'],
                "start": d.isoformat(),
                "color": "#1E88E5",
                "extendedProps": {"scripts": row['Related_Scripts']}
            })
            
        calendar(events=cal_events, options={"initialDate": f"2026-{sel_month:02d}-01", "editable": not is_locked})

with tab2:
    st.header("Step 2: Export for SAP")
    if not st.session_state.master_data.empty:
        sap_rows = []
        # Calculate for ALL months
        for m in range(1, 13):
            for _, row in st.session_state.master_data.iterrows():
                target_date = get_sop_date(2026, m, row['WD_Offset'], logic_holidays)
                scripts = str(row['Related_Scripts']).split(';')
                for s in scripts:
                    sap_rows.append({
                        "SAP_Date": target_date.strftime("%Y%m%d"),
                        "Event": row['Event_Name'],
                        "Job_Script": s.strip(),
                        "WD": f"WD{row['WD_Offset']}"
                    })
        
        sap_df = pd.DataFrame(sap_rows)
        st.dataframe(sap_df, use_container_width=True)
        st.download_button("Export SAP CSV", sap_df.to_csv(index=False), "sap_upload.csv")
