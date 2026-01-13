import streamlit as st
import pandas as pd
import holidays
from datetime import date, timedelta
from streamlit_calendar import calendar

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="S&OP Logic Manager", layout="wide")

# Pre-load holidays (skips weekends + LUX/BEL)
years = [2025, 2026]
lu_hols = holidays.LU(years=years)
be_hols = holidays.BE(years=years)
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

def get_sop_date(year, month, wd, hols):
    count, curr = 0, date(year, month, 1)
    # Ensure wd is an integer
    wd = int(wd)
    while count < wd:
        if curr.weekday() < 5 and curr not in hols:
            count += 1
        if count < wd: 
            curr += timedelta(days=1)
    return curr

# --- 2. SESSION STATE INITIALIZATION ---
# This ensures the app remembers your data even when you switch tabs
if 'master_data' not in st.session_state:
    st.session_state.master_data = pd.DataFrame()

# --- 3. UI TABS ---
tab1, tab2, tab3 = st.tabs(["📅 S&OP Calendar View", "📂 SAP Job Export", "⚙️ Setup Logic"])

with tab3:
    st.header("Step 1: Upload Your Logic")
    st.info("Ensure your Excel has columns: **WD_Offset**, **Event_Name**, **Related_Scripts**")
    file = st.file_uploader("Upload Excel File", type=['xlsx'])
    
    if file:
        try:
            df = pd.read_excel(file)
            # Basic validation
            if all(col in df.columns for col in ['WD_Offset', 'Event_Name']):
                st.session_state.master_data = df
                st.success(f"Successfully loaded {len(df)} events!")
            else:
                st.error("Missing columns! Please check your Excel headers.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    if not st.session_state.master_data.empty:
        st.write("### Current Active Logic")
        st.dataframe(st.session_state.master_data, use_container_width=True)

with tab1:
    if st.session_state.master_data.empty:
        st.warning("⚠️ No data found. Please go to the 'Setup Logic' tab and upload your Excel file.")
    else:
        col1, col2 = st.columns([1, 4])
        with col1:
            sel_month = st.selectbox("Select Month", range(1, 13), index=date.today().month - 1)
            is_locked = st.toggle("Lock Events", value=True)
            st.caption("Unlock to drag events (visual only)")
        
        # Build Calendar Events
        cal_events = []
        for _, row in st.session_state.master_data.iterrows():
            try:
                # Calculate the date based on your workday logic
                d = get_sop_date(2026, sel_month, row['WD_Offset'], logic_holidays)
                cal_events.append({
                    "title": str(row['Event_Name']),
                    "start": d.isoformat(),
                    "color": "#1E88E5",
                    "allDay": True,
                    "extendedProps": {"scripts": str(row.get('Related_Scripts', ''))}
                })
            except Exception as e:
                continue # Skip rows with errors

        # THE FIX: We use a dynamic key based on the data length and selected month
        # This forces the calendar to re-render when data or month changes.
        calendar_key = f"cal_{len(cal_events)}_{sel_month}"
        
        calendar_options = {
            "initialDate": f"2026-{sel_month:02d}-01",
            "initialView": "dayGridMonth",
            "editable": not is_locked,
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        }
        
        state = calendar(events=cal_events, options=calendar_options, key=calendar_key)

with tab2:
    st.header("Step 2: Export for SAP")
    if not st.session_state.master_data.empty:
        sap_rows = []
        for m in range(1, 13):
            for _, row in st.session_state.master_data.iterrows():
                try:
                    target_date = get_sop_date(2026, m, row['WD_Offset'], logic_holidays)
                    scripts = str(row.get('Related_Scripts', '')).split(';')
                    for s in scripts:
                        if s.strip(): # Avoid empty scripts
                            sap_rows.append({
                                "SAP_Date": target_date.strftime("%Y%m%d"),
                                "Event": row['Event_Name'],
                                "Job_Script": s.strip(),
                                "WD_Logic": f"WD{row['WD_Offset']}"
                            })
                except:
                    continue
        
        sap_df = pd.DataFrame(sap_rows)
        st.dataframe(sap_df, use_container_width=True)
        st.download_button("📥 Download SAP CSV", sap_df.to_csv(index=False), "sap_upload.csv")
