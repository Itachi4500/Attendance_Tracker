import pandas as pd
import os

# Simulated file-based storage (could be replaced with a DB)
PROFILE_FILE = "employee_profiles.csv"

def load_profiles():
    """
    Load employee profiles from CSV. Create if not exists.
    """
    if not os.path.exists(PROFILE_FILE):
        df = pd.DataFrame(columns=["Employee ID", "Name", "Department"])
        df.to_csv(PROFILE_FILE, index=False)
    return pd.read_csv(PROFILE_FILE)

def save_profiles(df):
    """
    Save the updated profiles dataframe to disk.
    """
    df.to_csv(PROFILE_FILE, index=False)

def add_or_update_profile(emp_id, name, department):
    """
    Add a new employee profile or update an existing one.
    """
    df = load_profiles()
    if emp_id in df["Employee ID"].values:
        df.loc[df["Employee ID"] == emp_id, ["Name", "Department"]] = [name, department]
    else:
        df = df.append({"Employee ID": emp_id, "Name": name, "Department": department}, ignore_index=True)
    save_profiles(df)
    return df

def get_profile(emp_id):
    """
    Retrieve a single employee's profile as a dict.
    """
    df = load_profiles()
    profile = df[df["Employee ID"] == emp_id]
    return profile.to_dict(orient="records")[0] if not profile.empty else None

def list_profiles():
    """
    Return all employee profiles.
    """
    return load_profiles()

def get_employee_attendance(emp_id, attendance_df):
    """
    Filter the attendance log for a specific employee.
    """
    return attendance_df[attendance_df["Employee ID"] == emp_id]
