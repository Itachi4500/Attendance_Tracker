import pandas as pd
import os
from fpdf import FPDF

# Default configuration
CONFIG_FILE = "admin_config.csv"

def load_config():
    """
    Load working hour thresholds. Default: 9 AM - 5 PM, 8 hours.
    """
    if not os.path.exists(CONFIG_FILE):
        df = pd.DataFrame([{
            "Office Start": "09:00:00",
            "Office End": "17:00:00",
            "Daily Hours Required": 8
        }])
        df.to_csv(CONFIG_FILE, index=False)
    return pd.read_csv(CONFIG_FILE).iloc[0]

def update_config(start_time, end_time, required_hours):
    """
    Update configuration.
    """
    df = pd.DataFrame([{
        "Office Start": start_time,
        "Office End": end_time,
        "Daily Hours Required": required_hours
    }])
    df.to_csv(CONFIG_FILE, index=False)

def remove_employee(emp_id, profile_df):
    """
    Remove employee from profile list by ID.
    """
    new_df = profile_df[profile_df["Employee ID"] != emp_id]
    new_df.to_csv("employee_profiles.csv", index=False)
    return new_df

def export_to_csv(df, filename="attendance_log.csv"):
    df.to_csv(filename, index=False)
    return filename

def export_to_excel(df, filename="attendance_log.xlsx"):
    df.to_excel(filename, index=False)
    return filename

def export_to_pdf(df, filename="attendance_log.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header
    col_width = 40
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()
    
    # Rows
    for i in range(len(df)):
        for item in df.iloc[i]:
            pdf.cell(col_width, 10, str(item), border=1)
        pdf.ln()
    
    pdf.output(filename)
    return filename
