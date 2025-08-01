import datetime
import pandas as pd

# Define office rules
OFFICE_START = datetime.time(9, 0, 0)   # 9:00 AM
OFFICE_END = datetime.time(17, 0, 0)    # 5:00 PM
WORK_HOURS_PER_DAY = 8  # standard working hours

def get_working_hours(in_time, out_time):
    try:
        in_dt = datetime.datetime.strptime(in_time, "%H:%M:%S")
        out_dt = datetime.datetime.strptime(out_time, "%H:%M:%S")
        duration = out_dt - in_dt
        return round(duration.total_seconds() / 3600, 2)  # return hours (2 decimals)
    except:
        return 0.0

def check_late(in_time):
    try:
        in_dt = datetime.datetime.strptime(in_time, "%H:%M:%S").time()
        return in_dt > OFFICE_START
    except:
        return False

def check_early_logout(out_time):
    try:
        out_dt = datetime.datetime.strptime(out_time, "%H:%M:%S").time()
        return out_dt < OFFICE_END
    except:
        return False

def check_overtime(hours_worked):
    try:
        return hours_worked > WORK_HOURS_PER_DAY
    except:
        return False

def process_attendance_dataframe(df):
    """
    Adds columns for Hours Worked, Overtime, Late Arrival, Early Logout.
    Assumes 'Check-in Time' and 'Check-out Time' columns exist in HH:MM:SS format.
    """
    df["Hours Worked"] = df.apply(
        lambda row: get_working_hours(row["Check-in Time"], row["Check-out Time"]),
        axis=1
    )
    df["Late Arrival"] = df["Check-in Time"].apply(check_late)
    df["Early Logout"] = df["Check-out Time"].apply(check_early_logout)
    df["Overtime"] = df["Hours Worked"].apply(check_overtime)
    return df

def generate_monthly_summary(df):
    """
    Returns a grouped summary of total hours worked per employee per month.
    Assumes 'Date' is in YYYY-MM-DD format and 'Hours Worked' is already calculated.
    """
    df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M")
    summary = df.groupby(["Employee ID", "Name", "Month"])["Hours Worked"].sum().reset_index()
    summary["Hours Worked"] = summary["Hours Worked"].round(2)
    return summary
