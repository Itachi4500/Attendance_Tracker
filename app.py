import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os

# Utils
from utils.qrcode_utils import generate_qr_code, decode_qr_from_image
from utils.calculator import calculate_working_hours
from utils.profile import load_profiles, get_profile
from utils.admin_control import add_employee, remove_employee, export_data
from utils.notification import send_alert
from utils.security import generate_one_time_token, validate_token, get_public_ip, get_geo_location
from utils.accessibility import mobile_friendly_view, cross_platform_info

# Storage for this example
if "attendance_log" not in st.session_state:
    st.session_state.attendance_log = []

if "valid_tokens" not in st.session_state:
    st.session_state.valid_tokens = {}

# UI Setup
st.set_page_config(page_title="Employee Attendance Tracker", layout="wide")
mobile_friendly_view()
cross_platform_info()
st.title("📋 Employee Attendance Tracker with QR")

# Tabs
tabs = st.tabs(["Scan QR", "Real-Time Dashboard", "Add/Remove Employees", "Profiles", "Export"])

# ------------------- TAB 1: QR Scan ------------------ #
with tabs[0]:
    st.header("🔍 QR Scan for Check-In/Check-Out")
    uploaded_file = st.file_uploader("Upload or scan QR code:", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        token = decode_qr_from_image(uploaded_file)

        if validate_token(token, st.session_state.valid_tokens):
            emp_id = st.session_state.valid_tokens.get(token)
            profile = get_profile(emp_id)
            if profile:
                now = datetime.now()
                ip = get_public_ip()
                location = get_geo_location(ip)
                
                # Determine check-in or check-out
                today_logs = [log for log in st.session_state.attendance_log if log['emp_id'] == emp_id and log['date'] == now.date()]
                if not today_logs or today_logs[-1]['type'] == "Check-Out":
                    log_type = "Check-In"
                else:
                    log_type = "Check-Out"

                st.session_state.attendance_log.append({
                    "emp_id": emp_id,
                    "name": profile['name'],
                    "department": profile['department'],
                    "timestamp": now,
                    "type": log_type,
                    "date": now.date(),
                    "ip": ip,
                    "location": location
                })

                st.success(f"{log_type} recorded for {profile['name']} at {now.strftime('%H:%M:%S')}")
            else:
                st.error("Profile not found")
        else:
            st.error("Invalid or expired QR token")

# ---------------- TAB 2: Real-Time Dashboard ---------------- #
with tabs[1]:
    st.header("📊 Real-Time Attendance Dashboard")
    df = pd.DataFrame(st.session_state.attendance_log)

    if not df.empty:
        clocked_in = df.groupby("emp_id").tail(1)
        current = clocked_in[clocked_in["type"] == "Check-In"]
        st.subheader("✅ Currently Clocked In")
        st.dataframe(current[["emp_id", "name", "department", "timestamp"]])

        st.subheader("🕒 Working Hours Summary")
        summary = calculate_working_hours(df)
        st.dataframe(summary)
    else:
        st.info("No attendance records yet.")

# ---------------- TAB 3: Admin Controls ---------------- #
with tabs[2]:
    st.header("🔧 Admin: Add/Remove Employees")
    with st.form("add_form"):
        st.subheader("➕ Add Employee")
        name = st.text_input("Name")
        emp_id = st.text_input("Employee ID")
        department = st.text_input("Department")
        submitted = st.form_submit_button("Add")
        if submitted:
            add_employee(emp_id, name, department)
            st.success(f"Added {name} ({emp_id})")

    st.subheader("🗑 Remove Employee")
    profiles = load_profiles()
    selected = st.selectbox("Select Employee", [p['emp_id'] for p in profiles])
    if st.button("Remove"):
        remove_employee(selected)
        st.warning(f"Removed employee {selected}")

# ---------------- TAB 4: Profiles ---------------- #
with tabs[3]:
    st.header("👤 Employee Profiles")
    profiles = load_profiles()
    for profile in profiles:
        st.markdown(f"**ID:** {profile['emp_id']} | **Name:** {profile['name']} | **Department:** {profile['department']}")
        st.divider()

# ---------------- TAB 5: Export ---------------- #
with tabs[4]:
    st.header("📤 Export Attendance Logs")
    df = pd.DataFrame(st.session_state.attendance_log)
    if not df.empty:
        export_data(df)
    else:
        st.info("No data to export.")

