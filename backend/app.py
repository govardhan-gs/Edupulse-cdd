import sys
import os

# 1. Ensure Python can always locate the project root and sibling modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from datetime import date

# 2. Resilient imports that work both locally and inside Docker
try:
    from backend.models import (
        init_db,
        register_user,
        authenticate_user,
        add_assignment,
        get_user_assignments,
        toggle_assignment_completion
    )
    from backend.utils import (
        calculate_cie,
        calculate_see_needed,
        get_deadline_status
    )
except ModuleNotFoundError:
    from models import (
        init_db,
        register_user,
        authenticate_user,
        add_assignment,
        get_user_assignments,
        toggle_assignment_completion
    )
    from utils import (
        calculate_cie,
        calculate_see_needed,
        get_deadline_status
    )

# 3. Initialize database tables automatically
init_db()

# 4. Streamlit Page Configuration
st.set_page_config(
    page_title="EduPulse - Academic Dashboard",
    page_icon="⚡",
    layout="wide"
)

# 5. Session State for Authentication
if "user" not in st.session_state:
    st.session_state.user = None

# Custom helper for re-running
def refresh():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# -------------------------------------------------------------
# AUTHENTICATION SCREEN (LOGIN & REGISTRATION)
# -------------------------------------------------------------
if not st.session_state.user:
    st.title("⚡ EduPulse: Student Academic Performance & Assignment Tracker")
    st.markdown("Please log in with your university credentials or register a new student account.")
    
    col_auth, _ = st.columns([1, 1])
    
    with col_auth:
        mode = st.radio("Choose Action:", ["Login", "Register New Student"], horizontal=True)
        
        if mode == "Login":
            st.subheader("Student Login")
            usn_input = st.text_input("University Seat Number (USN):", placeholder="e.g. 4NI23CS001").strip().upper()
            pwd_input = st.text_input("Password:", type="password")
            
            if st.button("Log In", use_container_width=True):
                if authenticate_user(usn_input, pwd_input):
                    st.session_state.user = usn_input
                    st.success("Login successful!")
                    refresh()
                else:
                    st.error("Invalid USN or Password. (Default demo: 4NI23CS001 / password123)")
                    
        else:
            st.subheader("Student Registration")
            new_usn = st.text_input("Enter USN:", placeholder="e.g. 4NI23CS042").strip().upper()
            new_name = st.text_input("Full Name:", placeholder="e.g. John Doe").strip()
            new_pwd = st.text_input("Choose Password:", type="password")
            
            if st.button("Create Account", use_container_width=True):
                if not new_usn or not new_name or not new_pwd:
                    st.warning("Please fill out all fields.")
                else:
                    if register_user(new_usn, new_name, new_pwd):
                        st.success("Account created successfully! Please switch to Login.")
                    else:
                        st.error("USN already registered in the system.")

# -------------------------------------------------------------
# MAIN APPLICATION DASHBOARD (AUTHENTICATED)
# -------------------------------------------------------------
else:
    # Sidebar
    st.sidebar.title("⚡ EduPulse")
    st.sidebar.markdown(f"Logged in as: **`{st.session_state.user}`**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        refresh()

    st.title("🎓 Student Academic Performance & Smart Assignment Tracker")

    # Tabs for the two core modules
    tab_cie, tab_tracker = st.tabs([
        "📊 Module 1: CIE Performance Analyser",
        "📝 Module 2: Smart Assignment Deadline Tracker"
    ])

    # ---------------------------------------------------------
    # MODULE 1: CIE PERFORMANCE ANALYSER
    # ---------------------------------------------------------
    with tab_cie:
        st.header("CIE Marks Evaluation (NIE 2026-27 Scheme)")
        st.caption("Calculates total CIE out of 50 based on institutional weighting: Test Average (25) + Scaled Lab CIE (25)")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Input Component Marks")
            sub_select = st.selectbox("Select Subject:", [
                "Collaborative Dev & DevOps (1BCS303)",
                "Operating Systems",
                "Database Management Systems",
                "Discrete Mathematical Structures"
            ])
            t1 = st.slider("Test-1 Marks (Max 25):", 0.0, 25.0, 18.0, step=0.5)
            t2 = st.slider("Test-2 Marks (Max 25):", 0.0, 25.0, 20.0, step=0.5)
            lab = st.slider("Lab Continuous Evaluation (Max 50):", 0.0, 50.0, 42.0, step=1.0)

            cie_data = calculate_cie(t1, t2, lab)

        with col2:
            st.subheader("Performance & Eligibility Analysis")
            total_cie = cie_data["total_cie"]
            st.metric(label="Total Continuous Internal Evaluation (CIE)", value=f"{total_cie} / 50")

            if cie_data["is_eligible"]:
                st.success("✅ **Eligible for Semester End Examination (SEE)** (Satisfies ≥ 40% cutoff)")
            else:
                st.error("⚠️ **Ineligible for SEE** (Total CIE is below 20/50 cutoff threshold)")

            st.markdown("---")
            st.subheader("🎯 Semester End Exam (SEE) Target Predictor")
            target_grade = st.selectbox(
                "Select Target Grade:",
                ["S (90%+)", "A (80%+)", "B (70%+)", "Pass (40%+)"]
            )
            needed_see = calculate_see_needed(total_cie, target_grade)
            
            if needed_see <= 100:
                st.info(f"To achieve **{target_grade}**, you must score at least **{needed_see} / 100** in the Semester End Exam (SEE).")
            else:
                st.warning("Mathematically unreachable: Current CIE requires more than 100 in SEE for this grade.")

    # ---------------------------------------------------------
    # MODULE 2: SMART ASSIGNMENT DEADLINE TRACKER
    # ---------------------------------------------------------
    with tab_tracker:
        st.header("Smart Assignment Deadline Tracker")
        st.caption("Automatically compares current system date with assignment deadlines to show real-time status indicators.")

        # Assignment Creation
        with st.expander("➕ Add New Assignment / Lab Milestone", expanded=False):
            with st.form("new_assignment_form"):
                subject_name = st.selectbox("Subject:", [
                    "Collaborative Dev & DevOps (1BCS303)",
                    "Operating Systems",
                    "Database Management Systems",
                    "Discrete Mathematical Structures"
                ])
                assignment_title = st.text_input("Assignment Name / Milestone:", placeholder="e.g. Exp 6: GitHub Actions Workflow")
                due_date_val = st.date_input("Submission Deadline:", min_value=date.today())
                submitted = st.form_submit_button("Save Assignment")
                
                if submitted:
                    if not assignment_title:
                        st.warning("Please provide an assignment title.")
                    else:
                        add_assignment(st.session_state.user, subject_name, assignment_title, str(due_date_val))
                        st.success(f"Assignment '{assignment_title}' added successfully!")
                        refresh()

        # Display Assignments
        raw_assignments = get_user_assignments(st.session_state.user)

        if raw_assignments:
            display_list = []
            for item in raw_assignments:
                status_info = get_deadline_status(item["due_date"], bool(item["is_completed"]))
                display_list.append({
                    "ID": item["id"],
                    "Subject": item["subject"],
                    "Assignment": item["title"],
                    "Deadline": item["due_date"],
                    "Status Indicator": status_info["badge"],
                    "Done": bool(item["is_completed"])
                })

            df = pd.DataFrame(display_list)
            
            # Show summary metrics
            c_tot, c_done, c_pend = st.columns(3)
            c_tot.metric("Total Assignments", len(df))
            c_done.metric("Completed", len(df[df["Done"] == True]))
            c_pend.metric("Pending Action", len(df[df["Done"] == False]))

            st.dataframe(
                df[["ID", "Subject", "Assignment", "Deadline", "Status Indicator"]],
                use_container_width=True,
                hide_index=True
            )

            # Toggle Completion Status
            st.subheader("Update Submission Status")
            selected_ids = st.multiselect(
                "Select Assignment IDs to toggle completion:",
                options=[item["id"] for item in raw_assignments],
                format_func=lambda x: f"ID {x}: {next(a['title'] for a in raw_assignments if a['id'] == x)}"
            )

            if st.button("Toggle Status (Completed / Incomplete)"):
                for aid in selected_ids:
                    current_task = next(a for a in raw_assignments if a["id"] == aid)
                    new_val = 0 if current_task["is_completed"] else 1
                    toggle_assignment_completion(aid, new_val)
                st.success("Assignment status updated!")
                refresh()
        else:
            st.info("No assignments recorded yet. Use the '➕ Add New Assignment' section above to create one!")