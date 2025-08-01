import streamlit as st
import pandas as pd
import datetime
import qrcode
import io
import cv2
from PIL import Image

# Title
st.set_page_config(page_title="Attendance Tracker", layout="centered")
st.title("📋 Employee Attendance Tracker (QR Code Based)")

# Load or initialize attendance data
if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = pd.DataFrame(columns=["Employee ID", "Name", "Check-in Time", "Check-out Time", "Date"])

# QR Code Generator for Employee IDs
st.sidebar.header("🧾 Generate Employee QR Code")
emp_id = st.sidebar.text_input("Employee ID")
emp_name = st.sidebar.text_input("Employee Name")

if st.sidebar.button("Generate QR Code"):
    if emp_id:
        qr = qrcode.make(emp_id)
        buf = io.BytesIO()
        qr.save(buf)
        st.sidebar.image(buf.getvalue(), caption=f"QR for {emp_id}", use_column_width=True)
    else:
        st.sidebar.warning("Enter Employee ID first.")

# QR Code Scanner from Uploaded Image
st.header("📲 Scan QR Code to Check In/Out")
uploaded_file = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded QR", width=200)

    # Decode QR
    img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img_array)

    if data:
        # Check if already checked in
        today = datetime.date.today().strftime('%Y-%m-%d')
        emp_logs = st.session_state.attendance_df[
            (st.session_state.attendance_df["Employee ID"] == data) &
            (st.session_state.attendance_df["Date"] == today)
        ]

        current_time = datetime.datetime.now().strftime('%H:%M:%S')

        if emp_logs.empty:
            name_input = st.text_input("Enter your name to check in")
            if st.button("✅ Check In"):
                st.session_state.attendance_df = st.session_state.attendance_df.append({
                    "Employee ID": data,
                    "Name": name_input,
                    "Check-in Time": current_time,
                    "Check-out Time": "",
                    "Date": today
                }, ignore_index=True)
                st.success(f"{name_input} checked in at {current_time}")
        elif emp_logs.iloc[0]["Check-out Time"] == "":
            if st.button("📤 Check Out"):
                idx = emp_logs.index[0]
                st.session_state.attendance_df.at[idx, "Check-out Time"] = current_time
                st.success(f"Checked out at {current_time}")
        else:
            st.info("✅ You already checked out today.")
    else:
        st.error("❌ Invalid QR code.")

# Show current day attendance table
st.subheader("📊 Today's Attendance")
today = datetime.date.today().strftime('%Y-%m-%d')
today_df = st.session_state.attendance_df[st.session_state.attendance_df["Date"] == today]

st.dataframe(today_df, use_container_width=True)

# Download data
st.download_button("⬇️ Download Attendance Log", data=st.session_state.attendance_df.to_csv(index=False), file_name="attendance_log.csv", mime="text/csv")

