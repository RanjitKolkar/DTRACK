import streamlit as st
import pandas as pd
from db import init_db, get_conn
from utils import check_password, hash_password, get_user, log_action, create_user, ensure_default_admin
import admin, user_panel, subuser_panel
from datetime import datetime, timedelta

st.set_page_config(page_title='DTRACK', layout='wide')
init_db()
ensure_default_admin()

# Mobile-first CSS
st.markdown("""
<style>
/* Base */
:root { --brand:#005792; --bg:#f4f7fb; --ink:#002b45; }
[data-testid="stAppViewContainer"]{background:var(--bg);}
div[data-testid="stSidebar"]{background:#002b45;color:#fff;}
h1,h2,h3{color:var(--ink);}
.stButton>button{background-color:var(--brand);color:white;border-radius:10px;padding:10px 16px;}
.stTextInput>div>div>input,.stTextArea textarea,.stSelectbox>div>div{border-radius:10px;padding:10px;}

/* Mobile tweaks */
@media (max-width: 768px){
  .stButton>button{width:100%;}
  .block-container{padding-top:0.5rem;padding-left:0.6rem;padding-right:0.6rem;}
  h1{font-size:1.4rem;} h2{font-size:1.2rem;} h3{font-size:1.05rem;}
  [data-testid="stSidebarContent"] {font-size:0.95rem;}
  .stDataFrame{font-size:0.85rem;}
}
</style>
""", unsafe_allow_html=True)

st.title("💽 DTRACK ")
st.caption("DIAL - Digital Analytics & Intelligence Lab")

# session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None

try:
    if not st.session_state.logged_in:
        st.sidebar.title('Welcome')
        action = st.sidebar.radio('Action', ['Login','Register','About'])
        if action == 'About':
            st.sidebar.info('DTRACK prototype - register as a conducting team. Admin approves registrations.')
        if action == 'Register':
            st.header('Register - Conducting Team')
            with st.form('reg'):
                uname = st.text_input('Team Code / Username')
                pwd = st.text_input('Password', type='password')
                if st.form_submit_button('Register'):
                    if not uname or not pwd:
                        st.error('Provide username and password.')
                    else:
                        try:
                            create_user(uname, pwd, role='user', approved=0)
                            st.success('Registered. Await admin approval.')
                            log_action(uname, 'registered')
                        except Exception as e:
                            st.error('Registration failed: ' + str(e))
        if action == 'Login':
            st.header('Login')
            with st.form('login'):
                uname = st.text_input('Username')
                pwd = st.text_input('Password', type='password')
                if st.form_submit_button('Login'):
                    if not uname or not pwd:
                        st.error('Enter credentials.')
                    else:
                        try:
                            conn = get_conn(); c = conn.cursor()
                            row = c.execute('SELECT * FROM users WHERE username=?', (uname,)).fetchone()
                            if not row:
                                st.error('User not found.')
                            else:
                                if row['approved'] == 0:
                                    st.warning('Pending admin approval.')
                                else:
                                    if check_password(pwd, row['password_hash']):
                                        role = row['role']
                                        if role == 'subuser' and row['valid_till']:
                                            try:
                                                if datetime.fromisoformat(row['valid_till']) < datetime.utcnow():
                                                    st.error('Sub-user expired.')
                                                else:
                                                    st.session_state.logged_in = True; st.session_state.user = uname; st.session_state.role = role
                                                    log_action(uname, 'login_success')
                                                    st.rerun()
                                            except Exception:
                                                st.error('Invalid valid_till for account. Contact admin.')
                                        else:
                                            if row['password_expiry'] and datetime.fromisoformat(row['password_expiry']) < datetime.utcnow():
                                                st.warning('Password expired. Contact admin to reset.')
                                            else:
                                                st.session_state.logged_in = True; st.session_state.user = uname; st.session_state.role = role
                                                log_action(uname, 'login_success')
                                                st.rerun()
                                    else:
                                        st.error('Invalid password.')
                                        log_action(uname, 'login_failed')
                        except Exception as e:
                            st.error(f'Login error: {e}')
                        finally:
                            try:
                                conn.close()
                            except Exception:
                                pass
    else:
        # logged in
        st.sidebar.success(f"Logged in: {st.session_state.user}")
        if st.sidebar.button('Logout'):
            try:
                log_action(st.session_state.user, 'logout')
            except Exception:
                pass
            st.session_state.logged_in = False; st.session_state.user = None; st.session_state.role = None
            st.rerun()

        role = st.session_state.role; user = st.session_state.user
        # route
        if role == 'admin':
            admin.admin_panel(user)
        elif role == 'user':
            user_panel.user_panel(user)
        elif role == 'subuser':
            subuser_panel.subuser_panel(user)

        # common HDD form and view in main area (quick add)
        st.markdown('---')
        st.subheader('Quick HDD Add / Search')

        from scanner import scan_block
        try:
            scan_result = scan_block()
        except Exception as e:
            st.warning(f"Scanner unavailable: {e}")
            scan_result = None

        if scan_result:
            st.info(f"Scanned/Entered code: {scan_result}")
            st.session_state['serial_no'] = scan_result

        with st.expander('Add HDD (quick)'):
            with st.form('quick_hdd'):
                s_no = st.text_input('Serial No', value=(st.session_state.get('serial_no','')))
                space = st.selectbox('Unit Space', ['1TB','2TB','4TB','8TB'])
                tcode = st.text_input('Team Code', value=st.session_state.user if role=='user' else '')
                prem = st.text_input('Premise Name')
                dsearch = st.date_input('Date of Search')
                dseized = st.date_input('Date of Device Seized')
                details = st.text_area('Data Details')
                status = st.selectbox('Status', ['available','sealed','issued','returned'])
                if st.form_submit_button('Save'):
                    if not s_no or not tcode or not prem:
                        st.error('S.no, Team Code and Premise required.')
                    else:
                        try:
                            conn = get_conn(); c = conn.cursor()
                            now = datetime.utcnow().isoformat()
                            c.execute('INSERT INTO hdd_records (serial_no, unit_space, team_code, premise_name, date_search, date_seized, data_details, created_by, created_on, barcode_value, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                                      (s_no, space, tcode, prem, dsearch.isoformat(), dseized.isoformat(), details, st.session_state.user, now, s_no, status))
                            conn.commit(); conn.close()
                            st.success('Saved.')
                            log_action(st.session_state.user, f'quick_add:{s_no}')
                        except Exception as e:
                            st.error('Failed to save: ' + str(e))
        st.write('Use the role-specific panels for full features.')
except Exception as outer_e:
    st.error(f"Unexpected error: {outer_e}")
