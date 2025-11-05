import streamlit as st
import random, string

def _webcam_scanner():
    # Optional; never break if missing.
    try:
        from streamlit_webcam_qrcode_scanner import webcam_qrcode_scanner
        st.write("🎥 Webcam scanner available.")
        return webcam_qrcode_scanner(key="scanner")
    except Exception:
        return None

def _mock_code():
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SN-{token}"

def scan_block():
    st.subheader("📷 Scan / Enter Code")
    col1, col2, col3 = st.columns([2,1,1])

    manual = None
    with col1:
        manual = st.text_input("Manual entry (paste/type barcode/QR data)", key="manual_entry")

    mock = None
    with col2:
        if st.button("Mock Scan"):
            st.session_state['mock_code'] = _mock_code()
        mock = st.session_state.get('mock_code')

    webcam = None
    with col3:
        webcam = _webcam_scanner()

    if webcam:
        return webcam.strip()
    if manual:
        return manual.strip()
    if mock:
        return mock.strip()

    st.caption("Tip: Install `streamlit-webcam-qrcode-scanner` to enable live camera scanning.")
    return None
