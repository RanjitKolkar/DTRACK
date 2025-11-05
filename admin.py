import streamlit as st
import pandas as pd
from db import get_conn, get_columns
from utils import log_action, hash_password
from datetime import datetime, timedelta
import io, csv, json

def safe_dataframe(rows, table: str):
    try:
        if rows:
            return pd.DataFrame(rows, columns=rows[0].keys())
        cols = get_columns(table)
        return pd.DataFrame([], columns=cols)
    except Exception:
        return pd.DataFrame([])

def admin_panel(user):
    st.header("👑 Admin Panel")

    tabs = st.tabs(["Users", "Subusers", "Records", "Exports", "Logs"])

    # Users
    with tabs[0]:
        st.subheader("Approve / Manage Users")
        try:
            conn = get_conn(); c = conn.cursor()
            users = c.execute("SELECT username, role, approved, valid_till FROM users ORDER BY username").fetchall()
            conn.close()
        except Exception as e:
            st.error(f"DB error: {e}")
            users = []
        df = safe_dataframe(users, "users")
        st.dataframe(df, use_container_width=True)

        with st.form("approve_form"):
            uname = st.text_input("Username to approve")
            if st.form_submit_button("Approve"):
                try:
                    conn = get_conn(); c = conn.cursor()
                    c.execute("UPDATE users SET approved=1 WHERE username=?", (uname,))
                    conn.commit(); conn.close()
                    st.success(f"Approved {uname}")
                    log_action(user, f"approved:{uname}")
                except Exception as e:
                    st.error(f"Error: {e}")

        with st.form("reset_pass_form"):
            uname = st.text_input("Username to reset password")
            newp = st.text_input("New Password", type="password")
            if st.form_submit_button("Reset Password"):
                try:
                    conn = get_conn(); c = conn.cursor()
                    c.execute("UPDATE users SET password_hash=? WHERE username=?", (hash_password(newp), uname))
                    conn.commit(); conn.close()
                    st.success("Password reset")
                    log_action(user, f"reset_password:{uname}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Subusers
    with tabs[1]:
        st.subheader("Create Subuser")
        with st.form("subuser_form"):
            parent = st.text_input("Parent Team (for info)", value=user)
            uname = st.text_input("Subuser Username")
            pwd = st.text_input("Password", type="password")
            valid_days = st.number_input("Valid for (days)", 1, 365, 30)
            if st.form_submit_button("Create Subuser"):
                try:
                    conn = get_conn(); c = conn.cursor()
                    vt = (datetime.utcnow() + timedelta(days=int(valid_days))).isoformat()
                    pw_hash = hash_password(pwd)
                    c.execute("INSERT INTO users(username, password_hash, role, approved, valid_till) VALUES (?,?,?,?,?)",
                              (uname, pw_hash, 'subuser', 1, vt))
                    conn.commit(); conn.close()
                    st.success(f"Subuser {uname} created until {vt}")
                    log_action(user, f"created_subuser:{uname}")
                except Exception as e:
                    st.error(str(e))

    # Records
    with tabs[2]:
        st.subheader("All HDD Records")
        try:
            conn = get_conn(); c = conn.cursor()
            rows = c.execute("SELECT * FROM hdd_records ORDER BY id DESC").fetchall()
            conn.close()
        except Exception as e:
            st.error(f"DB error: {e}")
            rows = []
        df = safe_dataframe(rows, "hdd_records")
        st.dataframe(df, use_container_width=True, height=400)

    # Exports
    with tabs[3]:
        st.subheader("Export Records")
        opt = st.selectbox("Export format", ["CSV","JSON"])
        try:
            conn = get_conn(); c = conn.cursor()
            rows = c.execute("SELECT * FROM hdd_records ORDER BY id DESC").fetchall()
            conn.close()
            cols = rows[0].keys() if rows else get_columns("hdd_records")
        except Exception as e:
            st.error(f"DB error: {e}")
            rows = []; cols = get_columns("hdd_records")
        if st.button("Prepare Download"):
            if opt == "CSV":
                buf = io.StringIO()
                writer = csv.writer(buf)
                writer.writerow(cols)
                for r in rows:
                    writer.writerow([r.get(k, None) if isinstance(r, dict) else r[k] for k in cols])
                st.download_button("Download CSV", buf.getvalue(), "records.csv", "text/csv")
            else:
                data = [dict(r) for r in rows]
                st.download_button("Download JSON", json.dumps(data, indent=2), "records.json", "application/json")

    # Logs
    with tabs[4]:
        st.subheader("Logs (latest 1000)")
        try:
            conn = get_conn(); c = conn.cursor()
            rows = c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 1000").fetchall()
            conn.close()
        except Exception as e:
            st.error(f"DB error: {e}")
            rows = []
        df = safe_dataframe(rows, "logs")
        st.dataframe(df, use_container_width=True, height=300)
