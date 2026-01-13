import streamlit as st
import pandas as pd
import holidays
from datetime import date, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="S&OP Master Calendar", layout="wide")

# --- 1. HOLIDAY ENGINE ---
years = [2025, 2026]
lu_hols = holidays.LU(years=years)
be_hols = holidays.BE(years=years)
us_hols = holidays.US(years=years)
# Logic skips weekends + LUX/BEL only
logic_holidays = set(lu_hols.keys()) | set(be_hols.keys())

def get_sop_date(year, month, wd, hols):
    count, curr = 0, date(year, month, 1)
    wd = int(wd)
    while count < wd:
        if curr.weekday() < 5 and curr not in hols:
            count += 1
        if count < wd: 
            curr += timedelta(days=1)
    return curr

# --- 2. DATA PERSISTENCE ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = pd.DataFrame()

# --- 3. UI TABS ---
tab1, tab2, tab3 = st.tabs(["📅 S&OP Calendar", "📂 SAP Export", "⚙️ Setup"])

with tab3:
    st.header("Upload Logic")
    file = st.file_uploader("Upload Excel", type=['xlsx'])
    if file:
        st.session_state.master_data = pd.read_excel(file)
        st.success("Logic Loaded!")

with tab1:
    if st.session_state.master_data.empty:
        st.warning("Please upload your Excel logic in the Setup tab.")
    else:
        col1, col2 = st.columns([1, 4])
        with col1:
            sel_month = st.selectbox("Select Month", range(1, 13), index=date.today().month - 1)
            st.markdown("---")
            st.write("🌍 **Legend**")
            st.caption("🔵 S&OP Event")
            st.caption("🔴 LUX Holiday")
            st.caption("🟡 BEL Holiday")
            st.caption("🟢 USA Holiday")
        
        # --- MERGING EVENTS & HOLIDAYS ---
        cal_events = []
        
        # A. Add S&OP Events from Excel
        for _, row in st.session_state.master_data.iterrows():
            d = get_sop_date(2026, sel_month, row['WD_Offset'], logic_holidays)
            cal_events.append({
                "title": f"S&OP: {row['Event_Name']}",
                "start": d.isoformat(),
                "color": "#1E88E5", # Blue
                "allDay": True
            })
            
        # B. Add Regional Holidays to the UI
        for country, h_list, color in [("LU", lu_hols, "#FF5252"), ("BE", be_hols, "#FFD740"), ("US", us_hols, "#4CAF50")]:
            for d, h_name in h_list.items():
                if d.year == 2026 and d.month == sel_month:
                    cal_events.append({
                        "title": f"🚩 {country}: {h_name}",
                        "start": d.isoformat(),
                        "color": color,
                        "allDay": True
                    })

        calendar_key = f"cal_merged_{len(cal_events)}_{sel_month}"
        calendar_options = {
            "initialDate": f"2026-{sel_month:02d}-01",
            "initialView": "dayGridMonth",
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        }
        
        calendar(events=cal_events, options=calendar_options, key=calendar_key)

with tab2:
    # (SAP Export logic remains the same as previous version)
    st.header("SAP Script List")
    if not st.session_state.master_data.empty:
        sap_rows = []
        for m in range(1, 13):
            for _, row in st.session_state.master_data.iterrows():
                target_date = get_sop_date(2026, m, row['WD_Offset'], logic_holidays)
                scripts = str(row.get('Related_Scripts', '')).split(';')
                for s in scripts:
                    if s.strip() != 'nan' and s.strip():
                        sap_rows.append({
                            "Date": target_date.strftime("%Y%m%d"),
                            "Event": row['Event_Name'],
                            "Script": s.strip()
                        })
        st.dataframe(pd.DataFrame(sap_rows), use_container_width=True)
