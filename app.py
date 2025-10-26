import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Logger function
def log_activity(activity):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("activity_log.txt", "a") as f:
        f.write(f"{timestamp}: {activity}\n")

# Authentication setup (simple example; in production, use secure hashes)
names = ["Admin"]
usernames = ["admin"]
passwords = ["password"]  # Hash in production
hashed_passwords = stauth.Hasher(passwords).generate()
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "data_analysis", "abcdef", cookie_expiry_days=30)

# Main app
def main():
    st.title("Data Analysis Assistant")
    
    # Authentication
    name, authentication_status, username = authenticator.login("Login", "main")
    if authentication_status == False:
        st.error("Username/password is incorrect")
        return
    if authentication_status == None:
        st.warning("Please enter your username and password")
        return
    if authentication_status:
        authenticator.logout("Logout", "main")
        st.write(f"Welcome, {name}!")
        log_activity(f"User {username} logged in")
        
        # Sidebar for navigation
        menu = ["Upload Dataset", "EDA", "Modeler", "Visualization", "Activity Log"]
        choice = st.sidebar.selectbox("Menu", menu)
        
        # Global data storage
        if "data" not in st.session_state:
            st.session_state.data = None
        
        if choice == "Upload Dataset":
            st.header("Upload Dataset")
            uploaded_file = st.file_uploader("Choose a file (CSV, Excel, JSON)", type=["csv", "xlsx", "json"])
            if uploaded_file is not None:
                if uploaded_file.name.endswith(".csv"):
                    st.session_state.data = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith(".xlsx"):
                    st.session_state.data = pd.read_excel(uploaded_file)
                elif uploaded_file.name.endswith(".json"):
                    st.session_state.data = pd.read_json(uploaded_file)
                st.success("Dataset uploaded successfully!")
                st.dataframe(st.session_state.data.head())
                log_activity(f"Dataset uploaded: {uploaded_file.name}")
        
        elif choice == "EDA":
            if st.session_state.data is None:
                st.error("Please upload a dataset first.")
            else:
                st.header("Exploratory Data Analysis")
                data = st.session_state.data
                
                # Data Overview
                st.subheader("Data Overview")
                st.write(f"Shape: {data.shape}")
                st.write(f"Columns: {list(data.columns)}")
                
                # Column Types
                st.subheader("Column Types")
                st.write(data.dtypes)
                
                # Summary Statistics
                st.subheader("Summary Statistics")
                st.write(data.describe())
                
                # Missing Values
                st.subheader("Missing Values")
                st.write(data.isnull().sum())
                
                # Unique Values
                st.subheader("Unique Values per Column")
                for col in data.columns:
                    st.write(f"{col}: {data[col].nunique()}")
                
                # Correlation Matrix
                st.subheader("Correlation Matrix")
                numeric_data = data.select_dtypes(include=[np.number])
                if not numeric_data.empty:
                    corr = numeric_data.corr()
                    st.write(corr)
                else:
                    st.write("No numeric columns for correlation.")
                
                # Value Counts for Categorical Columns
                st.subheader("Value Counts for Categorical Columns")
                cat_cols = data.select_dtypes(include=["object"]).columns
                for col in cat_cols:
                    st.write(f"{col}:")
                    st.write(data[col].value_counts())
                
                # Skewness and Kurtosis
                st.subheader("Skewness and Kurtosis")
                if not numeric_data.empty:
                    st.write(f"Skewness: {numeric_data.skew()}")
                    st.write(f"Kurtosis: {numeric_data.kurtosis()}")
                
                # Top & Bottom Records
                st.subheader("Top & Bottom Records")
                st.write("Top 5:")
                st.dataframe(data.head())
                st.write("Bottom 5:")
                st.dataframe(data.tail())
                
                log_activity("EDA performed")
        
        elif choice == "Modeler":
            if st.session_state.data is None:
                st.error("Please upload a dataset first.")
            else:
                st.header("Modeler")
                data = st.session_state.data
                target = st.selectbox("Select Target Column", data.columns)
                features = st.multiselect("Select Feature Columns", [col for col in data.columns if col != target])
                
                if st.button("Train Model"):
                    if not features or target not in data.columns:
                        st.error("Select valid features and target.")
                    else:
                        X = data[features]
                        y = data[target]
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                        
                        model_type = st.selectbox("Model Type", ["Linear Regression", "Random Forest"])
                        if model_type == "Linear Regression":
                            model = LinearRegression()
                        else:
                            model = RandomForestRegressor()
                        
                        model.fit(X_train, y_train)
                        predictions = model.predict(X_test)
                        mse = mean_squared_error(y_test, predictions)
                        st.write(f"Mean Squared Error: {mse}")
                        log_activity(f"Model trained: {model_type}")
        
        elif choice == "Visualization":
            if st.session_state.data is None:
                st.error("Please upload a dataset first.")
            else:
                st.header("Visualization")
                data = st.session_state.data
                viz_type = st.selectbox("Select Visualization", ["Histogram", "Heatmap", "Bar Chart", "Pie Chart", "Bubble Chart"])
                
                if viz_type == "Histogram":
                    col = st.selectbox("Select Column", data.columns)
                    fig = px.histogram(data, x=col)
                    st.plotly_chart(fig)
                
                elif viz_type == "Heatmap":
                    numeric_data = data.select_dtypes(include=[np.number])
                    if not numeric_data.empty:
                        fig = px.imshow(numeric_data.corr(), text_auto=True)
                        st.plotly_chart(fig)
                    else:
                        st.error("No numeric data for heatmap.")
                
                elif viz_type == "Bar Chart":
                    col = st.selectbox("Select Column", data.columns)
                    fig = px.bar(data[col].value_counts())
                    st.plotly_chart(fig)
                
                elif viz_type == "Pie Chart":
                    col = st.selectbox("Select Column", data.columns)
                    fig = px.pie(data, names=col)
                    st.plotly_chart(fig)
                
                elif viz_type == "Bubble Chart":
                    x_col = st.selectbox("X-axis", data.columns)
                    y_col = st.selectbox("Y-axis", data.columns)
                    size_col = st.selectbox("Size", data.columns)
                    fig = px.scatter(data, x=x_col, y=y_col, size=size_col)
                    st.plotly_chart(fig)
                
                log_activity(f"Visualization created: {viz_type}")
        
        elif choice == "Activity Log":
            st.header("Activity Log")
            if os.path.exists("activity_log.txt"):
                with open("activity_log.txt", "r") as f:
                    logs = f.read()
                st.text_area("Logs", logs, height=300)
            else:
                st.write("No logs yet.")

if __name__ == "__main__":
    main()
