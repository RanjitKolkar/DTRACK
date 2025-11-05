import streamlit as st
import pandas as pd
from db import get_conn, get_columns
from utils import log_action
from datetime import datetime
import io, csv

def safe_dataframe(rows, table: str):
    try:
        if rows:
            return pd.DataFrame(rows, columns=rows[0].keys())
        cols = get_columns(table)
        return pd.DataFrame([], columns=cols)
    except Exception:
        return pd.DataFrame([])

def subuser_panel(user):
    st.header("🧑‍💻 Subuser Panel")
    st.caption("Limited access: add/search records.")

    tab1, tab2 = st.tabs(["Add", "Search"])

    with tab1:
        with st.form("add_form_sub"):
            s_no = st.text_input("Serial No")
            space = st.selectbox('Unit Space', ['1TB','2TB','4TB','8TB'])
            tcode = st.text_input('Team Code', value=user)
            prem = st.text_input('Premise Name')
            dsearch = st.date_input('Date of Search')
            dseized = st.date_input('Date of Device Seized')
            details = st.text_area('Data Details')
            status = st.selectbox('Status', ['available','sealed','issued','returned'])
            if st.form_submit_button("Save"):
                if not s_no or not tcode or not prem:
                    st.error("S.no, Team Code and Premise required.")
                else:
                    try:
                        conn = get_conn(); c = conn.cursor()
                        now = datetime.utcnow().isoformat()
                        c.execute('INSERT INTO hdd_records (serial_no, unit_space, team_code, premise_name, date_search, date_seized, data_details, created_by, created_on, barcode_value, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                                  (s_no, space, tcode, prem, dsearch.isoformat(), dseized.isoformat(), details, user, now, s_no, status))
                        conn.commit(); conn.close()
                        st.success("Saved.")
                        log_action(user, f"subuser_add:{s_no}")
                    except Exception as e:
                        st.error("Failed to save: " + str(e))

    with tab2:
        sn = st.text_input("Serial contains")
        if st.button("Search"):
            try:
                conn = get_conn(); c = conn.cursor()
                rows = c.execute("SELECT * FROM hdd_records WHERE serial_no LIKE ? ORDER BY id DESC LIMIT 200", (f"%{sn}%",)).fetchall()
                conn.close()
            except Exception as e:
                st.error(f"DB error: {e}")
                rows = []
            df = safe_dataframe(rows, "hdd_records")
            st.dataframe(df, use_container_width=True, height=300)
