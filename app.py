# QR Attendance System in Streamlit
# This script combines the functionality of the HTML, server.js, and database.sql files
# into a single Python application using the Streamlit framework.

import streamlit as st
import mysql.connector
import pandas as pd
import qrcode
from PIL import Image
import io
import base64
from datetime import datetime, date, time
import cv2
from pyzbar import pyzbar
import time as py_time
import numpy as np
import plotly.express as px

# --- DATABASE CONFIGURATION & SETUP ---
# IMPORTANT: Replace these with your actual database credentials.
DB_HOST = "localhost"
DB_USER = "postgres"  # e.g., 'root'
DB_PASSWORD = "1206"  # e.g., 'password'
DB_NAME = "attendance_db"
LATE_CHECK_IN_TIME = time(9, 30)

# Function to get a database connection
def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database: {err}")
        st.stop()

# Function to initialize the database and create tables if they don't exist
def setup_database():
    """
    Sets up the database. Creates the database if it doesn't exist and
    then creates the necessary tables.
    """
    try:
        # Connect to MySQL server without specifying a database
        conn_server = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn_server.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn_server.close()

        # Now connect to the specific database
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL commands from your database.sql file
        create_employees_table = """
        CREATE TABLE IF NOT EXISTS employees (
            id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            position VARCHAR(255) NOT NULL,
            department VARCHAR(255) NOT NULL,
            dob DATE NOT NULL
        );
        """
        create_attendance_table = """
        CREATE TABLE IF NOT EXISTS attendance (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id VARCHAR(20),
            check_in DATETIME,
            check_out DATETIME,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_employees_table)
        cursor.execute(create_attendance_table)
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        st.error(f"Database setup failed: {err}")
        st.stop()


# --- EMPLOYEE MANAGEMENT FUNCTIONS ---

def get_all_employees():
    """Fetches all employees from the database."""
    conn = get_db_connection()
    query = "SELECT id, name, position, department, dob FROM employees ORDER BY name"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def add_employee(id, name, position, department, dob):
    """Adds a new employee to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO employees (id, name, position, department, dob) VALUES (%s, %s, %s, %s, %s)"
    try:
        cursor.execute(query, (id, name, position, department, dob))
        conn.commit()
        st.toast(f"Employee '{name}' added successfully!", icon="✅")
    except mysql.connector.Error as err:
        st.toast(f"Error adding employee: {err}", icon="❌")
    finally:
        conn.close()

def update_employee(id, name, position, department, dob):
    """Updates an existing employee's details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE employees SET name = %s, position = %s, department = %s, dob = %s WHERE id = %s"
    try:
        cursor.execute(query, (name, position, department, dob, id))
        conn.commit()
        st.toast(f"Employee '{name}' updated successfully!", icon="🔄")
    except mysql.connector.Error as err:
        st.toast(f"Error updating employee: {err}", icon="❌")
    finally:
        conn.close()

def delete_employee(id, name):
    """Deletes an employee from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM employees WHERE id = %s"
    try:
        cursor.execute(query, (id,))
        conn.commit()
        st.toast(f"Employee '{name}' deleted.", icon="🗑️")
    except mysql.connector.Error as err:
        st.toast(f"Error deleting employee: {err}", icon="❌")
    finally:
        conn.close()

def generate_qr_code_image(employee_id):
    """Generates a QR code image for a given employee ID."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f'{{"employeeId": "{employee_id}"}}')
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# --- ATTENDANCE FUNCTIONS ---

def get_attendance_records(employee_id=None, start_date=None, end_date=None):
    """Fetches attendance records, optionally filtered by employee and date."""
    conn = get_db_connection()
    query = """
        SELECT a.record_id, a.employee_id, e.name as employee_name, a.check_in, a.check_out
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
    """
    conditions = []
    params = []

    if employee_id and employee_id != 'all':
        conditions.append("a.employee_id = %s")
        params.append(employee_id)
    if start_date:
        conditions.append("DATE(a.check_in) >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("DATE(a.check_in) <= %s")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY a.check_in DESC"

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def record_attendance(employee_id):
    """Records check-in or check-out for an employee."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = date.today().isoformat()

    # Find the last record for today
    query_last_record = """
        SELECT record_id, check_out FROM attendance
        WHERE employee_id = %s AND DATE(check_in) = %s
        ORDER BY check_in DESC LIMIT 1
    """
    cursor.execute(query_last_record, (employee_id, today_str))
    last_record = cursor.fetchone()

    employee_name_query = "SELECT name FROM employees WHERE id = %s"
    cursor.execute(employee_name_query, (employee_id,))
    employee_result = cursor.fetchone()
    employee_name = employee_result[0] if employee_result else "Unknown"


    if not last_record or last_record[1] is not None: # No record today or already checked out
        # Check In
        query_check_in = "INSERT INTO attendance (employee_id, check_in) VALUES (%s, NOW())"
        cursor.execute(query_check_in, (employee_id,))
        message = f"Checked In: {employee_name}"
        icon = "✅"
    else:
        # Check Out
        record_id = last_record[0]
        query_check_out = "UPDATE attendance SET check_out = NOW() WHERE record_id = %s"
        cursor.execute(query_check_out, (record_id,))
        message = f"Checked Out: {employee_name}"
        icon = "👋"

    conn.commit()
    conn.close()
    return message, icon


# --- UI HELPER FUNCTIONS ---
def calculate_hours_worked(row):
    """Calculates hours worked from a DataFrame row."""
    if pd.notna(row['check_in']) and pd.notna(row['check_out']):
        return round((row['check_out'] - row['check_in']).total_seconds() / 3600, 2)
    return 0.0

# --- STREAMLIT UI LAYOUT ---

st.set_page_config(page_title="QR Attendance System", page_icon="✅", layout="wide")

# Run DB setup
setup_database()

st.title("Advanced QR Attendance System")
st.markdown("A real-time attendance scanning and reporting solution.")

# Initialize session state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if 'scanner_active' not in st.session_state:
    st.session_state.scanner_active = False

tabs = ["Dashboard", "Scan QR", "Reports", "Employees"]
active_tab = st.sidebar.radio("Navigation", tabs)


# --- DASHBOARD TAB ---
if active_tab == "Dashboard":
    st.header("Dashboard")
    
    # Fetch data
    employees_df = get_all_employees()
    today_attendance_df = get_attendance_records(start_date=date.today(), end_date=date.today())

    # Metrics
    total_employees = len(employees_df)
    present_today = today_attendance_df['employee_id'].nunique()
    
    late_comers = 0
    if not today_attendance_df.empty:
        today_attendance_df['check_in_time'] = pd.to_datetime(today_attendance_df['check_in']).dt.time
        late_comers_df = today_attendance_df.loc[today_attendance_df.groupby('employee_id')['check_in_time'].idxmin()]
        late_comers = late_comers_df[late_comers_df['check_in_time'] > LATE_CHECK_IN_TIME].shape[0]

    checked_out_today = today_attendance_df.dropna(subset=['check_out'])
    avg_hours = 0
    if not checked_out_today.empty:
        checked_out_today['hours_worked'] = checked_out_today.apply(calculate_hours_worked, axis=1)
        avg_hours = round(checked_out_today['hours_worked'].mean(), 1)


    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Employees", total_employees)
    col2.metric("Present Today", present_today)
    col3.metric("Late Comers", late_comers)
    col4.metric("Avg Hours (Checked Out)", f"{avg_hours}h")

    st.divider()
    
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Today's Attendance")
        if not today_attendance_df.empty:
            display_df = today_attendance_df.copy()
            # Get the first check-in and last check-out for each employee for the day
            first_check_in = display_df.loc[display_df.groupby('employee_id')['check_in'].idxmin()]
            last_check_out = display_df.loc[display_df.groupby('employee_id')['check_out'].idxmax()]

            summary_df = pd.merge(
                first_check_in[['employee_name', 'check_in']],
                last_check_out[['employee_name', 'check_out']],
                on='employee_name',
                how='left'
            )
            summary_df['check_in'] = pd.to_datetime(summary_df['check_in']).dt.strftime('%H:%M:%S')
            summary_df['check_out'] = pd.to_datetime(summary_df['check_out']).dt.strftime('%H:%M:%S').replace('NaT', 'Not signed out')
            summary_df['Status'] = 'Present'
            st.dataframe(summary_df[['employee_name', 'Status', 'check_in', 'check_out']], use_container_width=True)
        else:
            st.info("No attendance records for today yet.")

    with col2:
        st.subheader("Upcoming Birthdays")
        today = datetime.now()
        employees_df['dob_month'] = pd.to_datetime(employees_df['dob']).dt.month
        employees_df['dob_day'] = pd.to_datetime(employees_df['dob']).dt.day
        
        upcoming_birthdays = employees_df[
            (employees_df['dob_month'] == today.month) &
            (employees_df['dob_day'] >= today.day)
        ].sort_values(by='dob_day')

        if not upcoming_birthdays.empty:
            for _, row in upcoming_birthdays.iterrows():
                st.markdown(f"🎂 **{row['name']}** - {row['dob_day']}/{row['dob_month']}")
        else:
            st.info("No upcoming birthdays this month.")


# --- SCAN QR TAB ---
elif active_tab == "Scan QR":
    st.header("Scan Employee QR Code")
    st.info("Position the employee's QR code in front of the camera.")

    if 'scanner_active' not in st.session_state:
        st.session_state.scanner_active = False

    if st.button("Start Scanner", key="start_scan"):
        st.session_state.scanner_active = True
    
    if st.button("Stop Scanner", key="stop_scan"):
        st.session_state.scanner_active = False

    if st.session_state.scanner_active:
        image_container = st.empty()
        cap = cv2.VideoCapture(0) # Use camera 0

        if not cap.isOpened():
            st.error("Could not open camera. Please grant permissions and refresh.")
            st.session_state.scanner_active = False
        
        last_scan_time = 0
        scan_cooldown = 5 # Cooldown in seconds to prevent multiple scans

        while st.session_state.scanner_active:
            success, frame = cap.read()
            if not success:
                st.error("Failed to capture frame from camera.")
                break

            # Decode QR codes
            decoded_objects = pyzbar.decode(frame)
            for obj in decoded_objects:
                current_time = py_time.time()
                if current_time - last_scan_time > scan_cooldown:
                    try:
                        # The data is stored as bytes, so we need to decode it
                        qr_data_str = obj.data.decode('utf-8')
                        # The data is a JSON string: '{"employeeId": "emp..."}'
                        import json
                        qr_data = json.loads(qr_data_str)
                        employee_id = qr_data.get('employeeId')

                        if employee_id:
                            message, icon = record_attendance(employee_id)
                            st.toast(message, icon=icon)
                            last_scan_time = current_time # Update last scan time
                    except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                        st.toast("Invalid QR code format.", icon="❌")
                        last_scan_time = current_time
                    
                # Draw a bounding box around the QR code
                points = obj.polygon
                if len(points) > 4:
                    hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                    cv2.polylines(frame, [hull], True, (0, 255, 0), 3)
                else:
                    cv2.polylines(frame, [np.array(points, dtype=np.int32)], True, (0, 255, 0), 3)

            # Display the frame in Streamlit
            image_container.image(frame, channels="BGR", use_column_width=True)
            
            # Small delay to prevent high CPU usage
            py_time.sleep(0.1)
        
        cap.release()
        if not st.session_state.scanner_active:
            image_container.empty()
            st.info("Scanner stopped.")


# --- REPORTS TAB ---
elif active_tab == "Reports":
    st.header("Generate Attendance Report")
    
    employees_df = get_all_employees()
    employee_options = {'all': "All Employees"}
    employee_options.update({row['id']: row['name'] for _, row in employees_df.iterrows()})

    with st.form("report_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_employee = st.selectbox("Select Employee", options=list(employee_options.keys()), format_func=lambda x: employee_options[x])
        with col2:
            start_date = st.date_input("Start Date", value=None)
        with col3:
            end_date = st.date_input("End Date", value=None)
        
        submitted = st.form_submit_button("Generate Report")

    if submitted:
        if not start_date or not end_date:
            st.warning("Please select both a start and end date.")
        else:
            report_df = get_attendance_records(selected_employee, start_date, end_date)
            
            if report_df.empty:
                st.info("No data found for the selected criteria.")
            else:
                report_df['hours_worked'] = report_df.apply(calculate_hours_worked, axis=1)
                
                # Display Chart
                st.subheader("Report Chart: Hours Worked")
                chart_data = report_df.copy()
                chart_data['date'] = pd.to_datetime(chart_data['check_in']).dt.date

                if selected_employee == 'all':
                    # Aggregate hours by date for all employees
                    agg_chart_data = chart_data.groupby('date')['hours_worked'].sum().reset_index()
                    fig = px.bar(agg_chart_data, x='date', y='hours_worked', title="Total Hours Worked by All Employees")
                else:
                    # Show hours per day for a single employee
                    fig = px.bar(chart_data, x='date', y='hours_worked', title=f"Hours Worked by {employee_options[selected_employee]}")
                
                st.plotly_chart(fig, use_container_width=True)

                # Display Data Table
                st.subheader("Report Data")
                display_df = report_df[['date', 'employee_name', 'check_in', 'check_out', 'hours_worked']].copy()
                display_df.rename(columns={'date': 'Date', 'employee_name': 'Employee', 'check_in': 'Check-in', 'check_out': 'Check-out', 'hours_worked': 'Hours Worked'}, inplace=True)
                st.dataframe(display_df, use_container_width=True)

                # Export to CSV
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Export as CSV",
                    data=csv,
                    file_name=f"attendance_report_{start_date}_to_{end_date}.csv",
                    mime='text/csv',
                )

# --- EMPLOYEES TAB ---
elif active_tab == "Employees":
    st.header("Employee Management")
    
    employees_df = get_all_employees()

    with st.expander("Add New Employee", expanded=False):
        with st.form("add_employee_form", clear_on_submit=True):
            new_id = f"emp{int(py_time.time())}"
            new_name = st.text_input("Full Name")
            new_pos = st.text_input("Position")
            new_dept = st.text_input("Department")
            new_dob = st.date_input("Date of Birth", min_value=date(1950, 1, 1), max_value=date.today())
            
            add_submitted = st.form_submit_button("Save Employee")
            if add_submitted:
                if new_name and new_pos and new_dept and new_dob:
                    add_employee(new_id, new_name, new_pos, new_dept, new_dob)
                    st.rerun() # Refresh data
                else:
                    st.warning("Please fill all fields.")

    st.subheader("Employee List")

    if employees_df.empty:
        st.info("No employees found. Add a new employee to get started.")
    else:
        for index, row in employees_df.iterrows():
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{row['name']}**")
                st.caption(f"ID: {row['id']}")
            with col2:
                st.text(f"Position: {row['position']}")
                st.text(f"Department: {row['department']}")
            
            with col3:
                # Edit Button & Modal
                with st.expander("Edit"):
                    with st.form(f"edit_form_{row['id']}"):
                        st.text_input("Full Name", value=row['name'], key=f"name_{row['id']}")
                        st.text_input("Position", value=row['position'], key=f"pos_{row['id']}")
                        st.text_input("Department", value=row['department'], key=f"dept_{row['id']}")
                        st.date_input("Date of Birth", value=pd.to_datetime(row['dob']), key=f"dob_{row['id']}")
                        
                        if st.form_submit_button("Update"):
                            update_employee(
                                row['id'],
                                st.session_state[f"name_{row['id']}"],
                                st.session_state[f"pos_{row['id']}"],
                                st.session_state[f"dept_{row['id']}"],
                                st.session_state[f"dob_{row['id']}"],
                            )
                            st.rerun()

                # Delete Button
                if st.button("Delete", key=f"delete_{row['id']}", type="secondary"):
                    delete_employee(row['id'], row['name'])
                    st.rerun()

                # QR Code Button & Modal
                with st.expander("View QR"):
                    qr_img = generate_qr_code_image(row['id'])
                    
                    # Convert PIL image to bytes for download
                    buf = io.BytesIO()
                    qr_img.save(buf, format="PNG")
                    byte_im = buf.getvalue()

                    st.image(qr_img, caption=f"QR Code for {row['name']}", width=200)
                    st.download_button(
                        label="Download QR",
                        data=byte_im,
                        file_name=f"{row['name'].replace(' ', '_')}_QR.png",
                        mime="image/png"
                    )
