"""Streamlit frontend entry point."""

import json

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

APP_TITLE = "Smart Interview Coach"
APP_SUBTITLE = "AI-Powered Interview Preparation Platform"

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.subheader(APP_SUBTITLE)

# Initialize session state variables
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_auth_headers() -> dict:
    """Return the Authorization header for API requests."""
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def login_page() -> None:
    """Render the login form."""
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
                json={"email": email, "password": password},
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


def register_page() -> None:
    """Render the registration form."""
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
                json={"full_name": full_name, "email": email, "password": password},
            )
            if response.status_code == 201:
                st.success("Registration successful! Please login.")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                st.error(f"Registration failed: {error_msg}")
        except Exception as e:
            st.error(f"Error connecting to server: {e}")


def display_analysis_results(resume_id: int) -> None:
    """Fetch and display AI analysis results for the uploaded resume.

    Makes three separate API calls to get the full analysis,
    detected role, and extracted skills, then renders each section.
    """
    headers = get_auth_headers()

    # --- Section 1: Structured Analysis ---
    st.subheader("Resume Analysis")
    try:
        resp = requests.get(f"{API_BASE_URL}/resume/{resume_id}/analysis", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            analysis = data.get("analysis")
            if analysis:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Full Name**")
                    st.write(analysis.get("full_name", "N/A"))

                    st.markdown("**Email**")
                    st.write(analysis.get("email", "N/A"))

                    st.markdown("**Phone**")
                    st.write(analysis.get("phone", "N/A"))

                with col2:
                    certifications = analysis.get("certifications", [])
                    st.markdown("**Certifications**")
                    if certifications:
                        for cert in certifications:
                            st.write(f"• {cert}")
                    else:
                        st.write("None listed")

                # Education
                st.markdown("---")
                st.markdown("**Education**")
                education_list = analysis.get("education", [])
                if education_list:
                    for edu in education_list:
                        st.write(
                            f"• {edu.get('degree', '')} in {edu.get('field', '')} "
                            f"— {edu.get('institution', '')} ({edu.get('year', '')})"
                        )
                else:
                    st.write("No education details found.")

                # Experience
                st.markdown("**Experience**")
                experience_list = analysis.get("experience", [])
                if experience_list:
                    for exp in experience_list:
                        st.write(
                            f"• **{exp.get('role', '')}** at {exp.get('company', '')} "
                            f"({exp.get('duration', '')})"
                        )
                        if exp.get("description"):
                            st.caption(exp["description"])
                else:
                    st.write("No experience details found.")

                # Projects
                st.markdown("**Projects**")
                projects_list = analysis.get("projects", [])
                if projects_list:
                    for project in projects_list:
                        tech_str = ", ".join(project.get("technologies", []))
                        st.write(f"• **{project.get('name', '')}**: {project.get('description', '')}")
                        if tech_str:
                            st.caption(f"Technologies: {tech_str}")
                else:
                    st.write("No projects found.")
        else:
            st.warning("Could not load analysis results.")
    except Exception as e:
        st.error(f"Error fetching analysis: {e}")

    # --- Section 2: Detected Role ---
    st.subheader("Detected Job Role")
    try:
        resp = requests.get(f"{API_BASE_URL}/resume/{resume_id}/role", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            role = data.get("role")
            if role:
                st.success(f"Primary Role: **{role.get('primary_role', 'N/A')}**")

                alt_roles = role.get("alternative_roles", [])
                if alt_roles:
                    st.write("Alternative Roles: " + ", ".join(alt_roles))

                st.caption(f"Reason: {role.get('reason', '')}")
        else:
            st.warning("Could not load role detection results.")
    except Exception as e:
        st.error(f"Error fetching role: {e}")

    # --- Section 3: Skills ---
    st.subheader("Extracted Skills")
    try:
        resp = requests.get(f"{API_BASE_URL}/resume/{resume_id}/skills", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            skills = data.get("skills")
            if skills:
                skill_col1, skill_col2 = st.columns(2)
                with skill_col1:
                    for category in ["programming_languages", "frameworks", "libraries", "databases"]:
                        items = skills.get(category, [])
                        if items:
                            label = category.replace("_", " ").title()
                            st.markdown(f"**{label}**")
                            st.write(", ".join(items))

                with skill_col2:
                    for category in ["cloud_platforms", "developer_tools", "soft_skills"]:
                        items = skills.get(category, [])
                        if items:
                            label = category.replace("_", " ").title()
                            st.markdown(f"**{label}**")
                            st.write(", ".join(items))
        else:
            st.warning("Could not load skills data.")
    except Exception as e:
        st.error(f"Error fetching skills: {e}")


def upload_page() -> None:
    """Render the resume upload form and display AI analysis on success."""
    st.header("Upload Resume")
    st.write("Upload your resume in PDF format. (Max 5 MB)")
    st.info(
        "After uploading, the AI will automatically analyze your resume "
        "and extract your skills, experience, and best-fit job role."
    )

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if st.button("Upload and Analyze"):
        if not uploaded_file:
            st.error("Please select a file first.")
            return

        try:
            headers = get_auth_headers()
            files = {
                "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
            }

            with st.spinner("Uploading and analyzing your resume. This may take a moment..."):
                response = requests.post(
                    f"{API_BASE_URL}/resume/upload",
                    headers=headers,
                    files=files,
                )

            if response.status_code == 201:
                data = response.json()
                resume_id = data.get("resume_id")
                st.success("Resume uploaded and analyzed successfully!")
                st.write(f"Resume ID: **{resume_id}**")
                st.divider()

                # Display the full AI analysis results
                display_analysis_results(resume_id)

            else:
                error_msg = response.json().get("detail", "Unknown error")
                st.error(f"Upload failed: {error_msg}")
                if response.status_code == 401:
                    st.session_state["access_token"] = None
                    st.rerun()
        except Exception as e:
            st.error(f"Error connecting to server: {e}")


def logout_page() -> None:
    """Render the logout page."""
    st.header("Logout")
    if st.button("Logout"):
        st.session_state["access_token"] = None
        st.success("Logged out successfully.")
        st.rerun()


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

st.sidebar.header("Navigation")

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