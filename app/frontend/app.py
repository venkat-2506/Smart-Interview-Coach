"""Streamlit frontend entry point."""

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"

APP_TITLE = "Smart Interview Coach"
APP_SUBTITLE = "AI-Powered Interview Preparation Platform"

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.subheader(APP_SUBTITLE)

# Initialize session state for authentication token
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

def login_page():
    st.header("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        if not email or not password:
            st.error("Please enter both email and password.")
            return
            
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state["access_token"] = data["access_token"]
                st.success("Login successful!")
                st.rerun()
            else:
                error_msg = response.json().get("detail", "Unknown error")
                st.error(f"Login failed: {error_msg}")
        except Exception as e:
            st.error(f"Error connecting to server: {e}")

def register_page():
    st.header("Register")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Register"):
        if not full_name or not email or not password:
            st.error("Please fill in all fields.")
            return
            
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                json={"full_name": full_name, "email": email, "password": password}
            )
            
            if response.status_code == 201:
                st.success("Registration successful! Please login.")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                st.error(f"Registration failed: {error_msg}")
        except Exception as e:
            st.error(f"Error connecting to server: {e}")

def upload_page():
    st.header("Upload Resume")
    st.write("Upload your resume in PDF format. (Max 5MB)")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if st.button("Upload"):
        if not uploaded_file:
            st.error("Please select a file first.")
            return
            
        try:
            headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
            # The 'file' key must match the parameter name in the FastAPI endpoint
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            
            response = requests.post(
                f"{API_BASE_URL}/resume/upload",
                headers=headers,
                files=files
            )
            
            if response.status_code == 201:
                data = response.json()
                st.success("Resume uploaded successfully!")
                st.write(f"Stored File ID: {data.get('resume_id')}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                st.error(f"Upload failed: {error_msg}")
                # If unauthorized, clear token
                if response.status_code == 401:
                    st.session_state["access_token"] = None
                    st.rerun()
        except Exception as e:
            st.error(f"Error connecting to server: {e}")

def logout_page():
    st.header("Logout")
    if st.button("Logout"):
        st.session_state["access_token"] = None
        st.success("Logged out successfully.")
        st.rerun()

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")

# Show different navigation options based on authentication state
if st.session_state["access_token"] is None:
    page = st.sidebar.radio("Go to", ["Login", "Register"])
    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
else:
    page = st.sidebar.radio("Go to", ["Upload Resume", "Logout"])
    if page == "Upload Resume":
        upload_page()
    elif page == "Logout":
        logout_page()