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

def user_panel(user):
    st.header("👤 User Panel")

    tabs = st.tabs(["My Records", "Search", "Export"])

    with tabs[0]:
        st.subheader("My Recent Records")
        try:
            conn = get_conn(); c = conn.cursor()
            rows = c.execute("SELECT * FROM hdd_records WHERE created_by=? ORDER BY id DESC LIMIT 200", (user,)).fetchall()
            conn.close()
        except Exception as e:
            st.error(f"DB error: {e}")
            rows = []
        df = safe_dataframe(rows, "hdd_records")
        st.dataframe(df, use_container_width=True, height=300)

    with tabs[1]:
        st.subheader("Search by Serial / Team / Status")
        sn = st.text_input("Serial contains")
        tc = st.text_input("Team code contains")
        stt = st.selectbox("Status", ["","available","sealed","issued","returned"])
        if st.button("Search"):
            try:
                conn = get_conn(); c = conn.cursor()
                q = "SELECT * FROM hdd_records WHERE 1=1"
                params = []
                if sn:
                    q += " AND serial_no LIKE ?"; params.append(f"%{sn}%")
                if tc:
                    q += " AND team_code LIKE ?"; params.append(f"%{tc}%")
                if stt:
                    q += " AND status=?"; params.append(stt)
                q += " ORDER BY id DESC LIMIT 500"
                rows = c.execute(q, tuple(params)).fetchall()
                conn.close()
            except Exception as e:
                st.error(f"DB error: {e}")
                rows = []
            df = safe_dataframe(rows, "hdd_records")
            st.dataframe(df, use_container_width=True, height=350)

    with tabs[2]:
        st.subheader("Export My Records")
        if st.button("Download CSV"):
            try:
                conn = get_conn(); c = conn.cursor()
                rows = c.execute("SELECT * FROM hdd_records WHERE created_by=? ORDER BY id DESC", (user,)).fetchall()
                conn.close()
                cols = rows[0].keys() if rows else get_columns("hdd_records")
                buf = io.StringIO()
                writer = csv.writer(buf)
                writer.writerow(cols)
                for r in rows:
                    writer.writerow([r[k] for k in cols])
                st.download_button("Download", buf.getvalue(), "my_records.csv", "text/csv")
            except Exception as e:
                st.error(f"Export error: {e}")
