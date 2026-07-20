"""Streamlit frontend entry point."""

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

APP_TITLE = "Smart Interview Coach"
APP_SUBTITLE = "AI-Powered Interview Preparation Platform"

st.set_page_config(page_title=APP_TITLE, layout="wide")


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def init_session() -> None:
    """Initialise all session-state keys once per session."""
    defaults = {
        "access_token": None,
        "resume_id": None,
        "resume_analyzed": False,
        "chat_history": [],
        "interview_started": False,
        "interview_session_id": None,
        "interview_current_question": None,
        "interview_question_number": 1,
        "interview_stage": None,
        "interview_topic": None,
        "interview_difficulty": None,
        "interview_completed": False,
        "interview_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def is_logged_in() -> bool:
    """Return True if a JWT token is present in session state."""
    return bool(st.session_state.get("access_token"))


def get_auth_headers() -> dict:
    """Return the Authorization header for API requests."""
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}


def clear_session() -> None:
    """Wipe all session-state keys and reset to defaults."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()


def _is_connection_error(exc: Exception) -> bool:
    """Return True if the exception is a network connection failure."""
    msg = str(exc).lower()
    return "connectionerror" in type(exc).__name__.lower() or "connection" in msg


# ---------------------------------------------------------------------------
# Centered app header (always visible)
# ---------------------------------------------------------------------------

def render_header() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title(APP_TITLE)
        st.subheader(APP_SUBTITLE)
    st.divider()


# ---------------------------------------------------------------------------
# Auth pages  (shown when NOT logged in)
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
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["access_token"] = data["access_token"]
                st.rerun()
            else:
                error_msg = response.json().get("detail", "Login failed. Please try again.")
                st.error(error_msg)
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the server. Please make sure the backend is running.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


def register_page() -> None:
    """Render the registration form."""
    st.header("Register")
    full_name = st.text_input("Full Name", key="reg_full_name")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Register"):
        if not full_name or not email or not password:
            st.error("Please fill in all fields.")
            return
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                json={"full_name": full_name, "email": email, "password": password},
                timeout=10,
            )
            if response.status_code == 201:
                st.success("Registration successful! Please go to the Login tab to sign in.")
            else:
                error_msg = response.json().get("detail", "Registration failed. Please try again.")
                st.error(error_msg)
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the server. Please make sure the backend is running.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


def auth_screen() -> None:
    """Show Login / Register tabs for unauthenticated users."""
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        login_page()
    with tab_register:
        register_page()


# ---------------------------------------------------------------------------
# Protected pages (shown only when logged in)
# ---------------------------------------------------------------------------

def _handle_response_error(resp: requests.Response, context: str) -> bool:
    """
    Check for auth or server errors on a response.
    Returns True if caller should stop rendering.
    Clears session on 401/403 and triggers rerun.
    """
    if resp.status_code in (401, 403):
        clear_session()
        st.warning("Your session has expired. Please log in again.")
        st.rerun()
    if resp.status_code == 500:
        st.error(f"Server error while {context}. Please try again later.")
        return True
    if resp.status_code not in (200, 201):
        detail = resp.json().get("detail", f"Error while {context}.")
        st.error(detail)
        return True
    return False


def _build_faiss_index(resume_id: int) -> bool:
    """
    Build the FAISS index for a resume after upload.
    Returns True on success, False on failure.
    """
    try:
        headers = get_auth_headers()
        resp = requests.post(
            f"{API_BASE_URL}/resume/{resume_id}/index",
            headers=headers,
            timeout=60,
        )
        if resp.status_code == 200:
            return True
        detail = resp.json().get("detail", "Indexing failed.")
        st.warning(f"Resume uploaded but indexing failed: {detail}. The Knowledge Assistant may not work.")
        return False
    except requests.exceptions.ConnectionError:
        st.warning("Resume uploaded but could not build search index. Check your connection.")
        return False
    except Exception:
        st.warning("Resume uploaded but indexing encountered an error.")
        return False


def display_analysis_results(resume_id: int) -> None:
    """Fetch and display AI analysis results for the uploaded resume."""
    headers = get_auth_headers()

    # --- Section 1: Structured Analysis ---
    st.subheader("Resume Analysis")
    try:
        resp = requests.get(
            f"{API_BASE_URL}/resume/{resume_id}/analysis",
            headers=headers,
            timeout=30,
        )
        if _handle_response_error(resp, "loading analysis"):
            return
        data = resp.json()
        analysis = data.get("analysis")
        if not analysis:
            st.info(data.get("message", "Analysis not available."))
        else:
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

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the server to load analysis.")
    except Exception as e:
        st.error(f"Error loading analysis: {e}")

    # --- Section 2: Detected Role ---
    st.subheader("Detected Job Role")
    try:
        resp = requests.get(
            f"{API_BASE_URL}/resume/{resume_id}/role",
            headers=headers,
            timeout=30,
        )
        if _handle_response_error(resp, "loading role"):
            return
        data = resp.json()
        role = data.get("role")
        if not role:
            st.info(data.get("message", "Role not detected."))
        else:
            st.success(f"Primary Role: **{role.get('primary_role', 'N/A')}**")
            alt_roles = role.get("alternative_roles", [])
            if alt_roles:
                st.write("Alternative Roles: " + ", ".join(alt_roles))
            if role.get("reason"):
                st.caption(f"Reason: {role.get('reason')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the server to load role detection.")
    except Exception as e:
        st.error(f"Error loading role: {e}")

    # --- Section 3: Skills ---
    st.subheader("Extracted Skills")
    try:
        resp = requests.get(
            f"{API_BASE_URL}/resume/{resume_id}/skills",
            headers=headers,
            timeout=30,
        )
        if _handle_response_error(resp, "loading skills"):
            return
        data = resp.json()
        skills = data.get("skills")
        if not skills:
            st.info(data.get("message", "Skills not extracted."))
        else:
            skill_col1, skill_col2 = st.columns(2)
            with skill_col1:
                for category in ["programming_languages", "frameworks", "libraries", "databases"]:
                    items = skills.get(category, [])
                    if items:
                        st.markdown(f"**{category.replace('_', ' ').title()}**")
                        st.write(", ".join(items))
            with skill_col2:
                for category in ["cloud_platforms", "developer_tools", "soft_skills"]:
                    items = skills.get(category, [])
                    if items:
                        st.markdown(f"**{category.replace('_', ' ').title()}**")
                        st.write(", ".join(items))
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the server to load skills.")
    except Exception as e:
        st.error(f"Error loading skills: {e}")


def upload_page() -> None:
    """Render the resume upload form and display AI analysis on success."""
    st.header("Upload Resume")
    st.write("Upload your resume in PDF format. (Max 5 MB)")
    st.info(
        "After uploading, the AI will automatically analyze your resume and extract "
        "your skills, experience, and best-fit job role."
    )
    st.divider()

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if st.button("Upload and Analyze"):
        if not uploaded_file:
            st.error("Please select a file before uploading.")
            return

        try:
            headers = get_auth_headers()
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

            with st.spinner("Uploading and analyzing your resume. This may take a minute..."):
                response = requests.post(
                    f"{API_BASE_URL}/resume/upload",
                    headers=headers,
                    files=files,
                    timeout=120,
                )

            if response.status_code in (401, 403):
                clear_session()
                st.warning("Your session has expired. Please log in again.")
                st.rerun()
                return

            if response.status_code == 500:
                detail = response.json().get("detail", "")
                if "quota" in detail.lower() or "429" in detail:
                    st.error(
                        "The AI service is temporarily unavailable due to quota limits. "
                        "Please wait a few minutes and try again."
                    )
                else:
                    st.error("Server error during analysis. Please try again.")
                return

            if response.status_code != 201:
                error_msg = response.json().get("detail", "Upload failed. Please try again.")
                st.error(error_msg)
                return

            data = response.json()
            resume_id = data.get("resume_id")
            st.session_state["resume_id"] = resume_id
            st.success("Resume uploaded and analyzed successfully!")

            # Build FAISS index so Knowledge Assistant works
            with st.spinner("Building search index for the Knowledge Assistant..."):
                _build_faiss_index(resume_id)

            # Reset chat history when a new resume is uploaded
            st.session_state["chat_history"] = []
            st.session_state["resume_analyzed"] = True
            st.divider()
            display_analysis_results(resume_id)

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the server. Please make sure the backend is running.")
        except requests.exceptions.Timeout:
            st.error(
                "The request timed out. Resume analysis can take up to 2 minutes. "
                "Please try again."
            )
        except Exception as e:
            st.error(f"Unexpected error during upload: {e}")


def resume_rag_page() -> None:
    """Render the conversational Resume Knowledge Assistant."""
    if not st.session_state.get("resume_analyzed"):
        st.info(
            "No resume found in this session. "
            "Please upload your resume first via the 'Upload Resume' page."
        )
        return

    st.header("Resume Knowledge Assistant")
    st.write(
        "Ask anything about your resume — projects, experience, skills, "
        "certifications, education, interview preparation, or technical topics."
    )
    st.divider()

    # Example questions expander
    with st.expander("Example Questions", expanded=False):
        examples = [
            "Explain my Customer Churn Prediction project.",
            "Generate interview questions from my resume.",
            "Explain SQL joins.",
            "Explain my internship experience.",
            "What strengths does my resume highlight?",
            "What technical skills should I revise before interviews?",
            "How should I introduce myself in an interview?",
            "What questions can HR ask from my resume?",
        ]
        for ex in examples:
            st.write(f"- {ex}")

    st.divider()

    # Render existing conversation history
    for message in st.session_state["chat_history"]:
        role = message["role"]
        content = message["content"]
        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant"):
                st.markdown(content)

    # Chat input at the bottom
    user_input = st.chat_input("Ask anything about your resume...")

    if user_input and user_input.strip():
        question = user_input.strip()

        # Immediately display the user message
        with st.chat_message("user"):
            st.write(question)

        # Call the backend chat endpoint
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    headers = get_auth_headers()
                    payload = {
                        "question": question,
                        "history": st.session_state["chat_history"],
                        "top_k": 5,
                    }
                    resp = requests.post(
                        f"{API_BASE_URL}/resume/{st.session_state['resume_id']}/chat",
                        headers=headers,
                        json=payload,
                        timeout=60,
                    )

                    if resp.status_code in (401, 403):
                        clear_session()
                        st.warning("Your session has expired. Please log in again.")
                        st.rerun()
                        return

                    if resp.status_code == 422:
                        st.warning(
                            "The search index for your resume is missing. "
                            "Please go to 'Upload Resume' and re-upload your resume."
                        )
                        return

                    if _handle_response_error(resp, "generating answer"):
                        return

                    data = resp.json()
                    answer = data.get("answer", "I could not generate an answer. Please try again.")
                    st.markdown(answer)

                    # Append to history after successful response
                    st.session_state["chat_history"].append(
                        {"role": "user", "content": question}
                    )
                    st.session_state["chat_history"].append(
                        {"role": "assistant", "content": answer}
                    )

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Cannot connect to the server. Please make sure the backend is running."
                    )
                except requests.exceptions.Timeout:
                    st.error(
                        "The request timed out. Please try again."
                    )
                except Exception as e:
                    st.error(f"Unexpected error: {e}")


def interview_page() -> None:
    """Render the Interview Coach page."""
    if not st.session_state.get("resume_analyzed"):
        st.info("Please upload and analyze a resume first to prepare for the interview.")
        return

    st.header("Interview Coach")
    st.write(
        "Practice mock interviews or quick assessments customized for your target job role. "
        "The engine dynamically plans your interview and generates resume-aware questions."
    )
    st.divider()

    # Case 1: Setup interview
    if not st.session_state.get("interview_started") and not st.session_state.get("interview_completed"):
        role = st.text_input("Target Job Role", value="Software Engineer", placeholder="e.g. Frontend Developer, Data Scientist")
        mode = st.selectbox("Interview Mode", ["Mock Interview", "Quick Assessment"])
        
        # Audio / Video toggles for S3 extensions
        camera_enabled = st.toggle("Enable Camera Compatibility (Mock Interview only)", value=False)
        microphone_enabled = st.toggle("Enable Microphone Compatibility (Mock Interview only)", value=False)
        
        if st.button("Start Interview"):
            if not role.strip():
                st.error("Please specify a target job role.")
                return
            
            with st.spinner("Generating interview plan and first question..."):
                try:
                    headers = get_auth_headers()
                    payload = {
                        "role": role.strip(),
                        "mode": mode,
                        "camera_enabled": camera_enabled,
                        "microphone_enabled": microphone_enabled
                    }
                    resp = requests.post(
                        f"{API_BASE_URL}/interview/start",
                        headers=headers,
                        json=payload,
                        timeout=90,
                    )
                    
                    if resp.status_code in (401, 403):
                        clear_session()
                        st.warning("Your session has expired. Please log in again.")
                        st.rerun()
                        return
                    
                    if _handle_response_error(resp, "starting interview"):
                        return
                    
                    data = resp.json()
                    st.session_state["interview_session_id"] = data["session_id"]
                    st.session_state["interview_current_question"] = data["current_question"]
                    st.session_state["interview_question_number"] = data["current_question_number"]
                    st.session_state["interview_stage"] = data["current_stage"]
                    st.session_state["interview_topic"] = data["current_topic"]
                    st.session_state["interview_difficulty"] = data["current_difficulty"]
                    st.session_state["interview_started"] = True
                    st.session_state["interview_completed"] = False
                    st.rerun()
                    
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the server. Please make sure the backend is running.")
                except requests.exceptions.Timeout:
                    st.error("The request timed out. Please try again.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

    # Case 2: Active interview
    elif st.session_state.get("interview_started") and not st.session_state.get("interview_completed"):
        # Display session progress
        st.subheader(f"Question {st.session_state.interview_question_number}")
        
        stage_display = st.session_state.interview_stage.replace('_', ' ').title()
        st.caption(
            f"**Stage:** {stage_display}  |  "
            f"**Topic:** {st.session_state.interview_topic}  |  "
            f"**Difficulty:** {st.session_state.interview_difficulty.title()}"
        )
        
        # Display the current question in a clean bubble
        st.info(st.session_state.interview_current_question)
        
        user_answer = st.text_area("Your Response", key="active_user_answer", height=150, placeholder="Type your response here...")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Submit and Next"):
                if not user_answer.strip():
                    st.error("Please enter a response before submitting.")
                    return
                
                with st.spinner("Submitting answer and fetching next question..."):
                    try:
                        headers = get_auth_headers()
                        resp = requests.post(
                            f"{API_BASE_URL}/interview/{st.session_state.interview_session_id}/answer",
                            headers=headers,
                            json={"answer": user_answer.strip()},
                            timeout=60,
                        )
                        
                        if resp.status_code in (401, 403):
                            clear_session()
                            st.warning("Your session has expired. Please log in again.")
                            st.rerun()
                            return
                        
                        if _handle_response_error(resp, "submitting answer"):
                            return
                        
                        data = resp.json()
                        if data["completed"]:
                            st.session_state["interview_completed"] = True
                            st.session_state["interview_started"] = False
                            st.session_state["interview_message"] = data["message"]
                        else:
                            st.session_state["interview_current_question"] = data["next_question"]
                            st.session_state["interview_question_number"] = data["next_question_number"]
                            st.session_state["interview_stage"] = data["next_stage"]
                            st.session_state["interview_topic"] = data["next_topic"]
                            st.session_state["interview_difficulty"] = data["next_difficulty"]
                        
                        st.rerun()
                        
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to the server. Please make sure the backend is running.")
                    except requests.exceptions.Timeout:
                        st.error("The request timed out. Please try again.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")
        with col2:
            if st.button("End Interview"):
                with st.spinner("Ending interview..."):
                    try:
                        headers = get_auth_headers()
                        resp = requests.post(
                            f"{API_BASE_URL}/interview/{st.session_state.interview_session_id}/end",
                            headers=headers,
                            timeout=30,
                        )
                        if resp.status_code in (401, 403):
                            clear_session()
                            st.warning("Your session has expired. Please log in again.")
                            st.rerun()
                            return
                        
                        st.session_state["interview_completed"] = True
                        st.session_state["interview_started"] = False
                        st.session_state["interview_message"] = "Interview manually ended."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

    # Case 3: Completed interview
    elif st.session_state.get("interview_completed"):
        st.success("Interview Session Concluded")
        st.write(st.session_state.get("interview_message", "Thank you for completing the interview!"))
        
        if st.button("Start New Assessment"):
            st.session_state["interview_started"] = False
            st.session_state["interview_session_id"] = None
            st.session_state["interview_current_question"] = None
            st.session_state["interview_question_number"] = 1
            st.session_state["interview_stage"] = None
            st.session_state["interview_topic"] = None
            st.session_state["interview_difficulty"] = None
            st.session_state["interview_completed"] = False
            st.session_state["interview_message"] = None
            st.rerun()


def logout_page() -> None:
    """Clear the session and redirect to Login."""
    st.header("Logout")
    st.write("Click below to securely log out of your account.")
    if st.button("Logout"):
        clear_session()
        st.rerun()


# ---------------------------------------------------------------------------
# Main app routing
# ---------------------------------------------------------------------------

render_header()

if not is_logged_in():
    # Unauthenticated — show Login / Register only
    auth_screen()
else:
    # Authenticated — show protected sidebar and pages
    st.sidebar.header("Navigation")
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Go to",
        ["Upload Resume", "Resume Knowledge Assistant", "Interview Coach", "Logout"],
        key="nav_page",
    )

    if page == "Upload Resume":
        upload_page()
    elif page == "Resume Knowledge Assistant":
        resume_rag_page()
    elif page == "Interview Coach":
        interview_page()
    elif page == "Logout":
        logout_page()