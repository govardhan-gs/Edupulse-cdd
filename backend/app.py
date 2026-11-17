import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st  # type: ignore[import-not-found]
import pandas as pd  # type: ignore[import-not-found]
from datetime import date

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
        calculate_cie_integrated,
        calculate_cie_theory,
        calculate_see_needed,
        calculate_semester_sgpa,
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
        calculate_cie_integrated,
        calculate_cie_theory,
        calculate_see_needed,
        calculate_semester_sgpa,
        get_deadline_status
    )

init_db()

st.set_page_config(page_title="EduPulse - Student Dashboard", page_icon="⚡", layout="wide")

# ----------------- SEMESTER 3 COURSE DEFINITION -----------------
SUBJECTS_CONFIG = {
    "Applied Mathematics-III (1BMAT301)": {"credits": 3, "has_lab": False},
    "DDCO (1BCS302)": {"credits": 4, "has_lab": True},
    "Collaborative development and devops (1BCS303)": {"credits": 4, "has_lab": False},
    "Data structures and application (1BCS304)": {"credits": 4, "has_lab": True},
    "Object Oriented programming Java (1BCS305)": {"credits": 3, "has_lab": False},
    "Data Analytics and Visualization": {"credits": 3, "has_lab": True}
}

ALL_SUBJECT_NAMES = list(SUBJECTS_CONFIG.keys())

if "user" not in st.session_state:
    st.session_state.user = None

def refresh():
    if hasattr(st, "rerun"): st.rerun()
    else: st.experimental_rerun()

# ----------------- AUTHENTICATION -----------------
if not st.session_state.user:
    st.title("⚡ EduPulse: Academic Performance & Assignment Tracker")
    st.markdown("Please log in with your university credentials (e.g., `4NI23CS001` / `password123`).")
    
    col_auth, _ = st.columns([1, 1])
    with col_auth:
        mode = st.radio("Action:", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            usn_input = st.text_input("USN:", placeholder="e.g. 4NI23CS001").strip().upper()
            pwd_input = st.text_input("Password:", type="password")
            if st.button("Log In", use_container_width=True):
                if authenticate_user(usn_input, pwd_input):
                    st.session_state.user = usn_input
                    refresh()
                else:
                    st.error("Invalid credentials.")
        else:
            new_usn = st.text_input("USN:").strip().upper()
            new_name = st.text_input("Full Name:")
            new_pwd = st.text_input("Password:", type="password")
            if st.button("Create Account", use_container_width=True):
                if register_user(new_usn, new_name, new_pwd):
                    st.success("Account created! Please switch to Login.")
                else:
                    st.error("USN already exists.")

# ----------------- DASHBOARD -----------------
else:
    st.sidebar.title("⚡ EduPulse")
    st.sidebar.markdown(f"Logged in: **`{st.session_state.user}`**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        refresh()

    st.title("🎓 Student Academic Performance & Smart Assignment Tracker")

    tab1, tab2, tab3 = st.tabs([
        "📊 Module 1: CIE Performance Analyser",
        "🎯 Module 2: Semester SGPA Calculator",
        "📝 Module 3: Smart Assignment Deadline Tracker"
    ])

    # ----------------- TAB 1: CIE ANALYSER -----------------
    with tab1:
        st.header("CIE Marks Evaluation (3rd Sem CSE Scheme)")
        sub_select = st.selectbox("Select Subject:", ALL_SUBJECT_NAMES)
        cfg = SUBJECTS_CONFIG[sub_select]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Component Marks Input")
            t1 = st.slider("Test-1 Marks (Max 25):", 0.0, 25.0, 18.0, step=0.5)
            t2 = st.slider("Test-2 Marks (Max 25):", 0.0, 25.0, 20.0, step=0.5)

            if cfg["has_lab"]:
                st.info("ℹ️ **Integrated Course:** Evaluated as `(Test1 + Test2)/2 + Lab_CIE/2`")
                lab = st.slider("Lab CIE (Max 50):", 0.0, 50.0, 42.0, step=1.0)
                cie_data = calculate_cie_integrated(t1, t2, lab)
            else:
                st.info("ℹ️ **Theory Course:** Evaluated as `(Test1 + Test2)/2 + Assignment/2`")
                assign = st.slider("Assignment/Activity Marks (Max 50):", 0.0, 50.0, 40.0, step=1.0)
                cie_data = calculate_cie_theory(t1, t2, assign)

        with col2:
            st.subheader("Eligibility & Prediction")
            total_cie = cie_data["total_cie"]
            st.metric("Total CIE Marks", f"{total_cie} / 50")

            if cie_data["is_eligible"]:
                st.success("✅ **Eligible for Semester End Examination (SEE)** (Satisfies ≥ 40% cutoff)")
            else:
                st.error("⚠️ **Ineligible for SEE** (Total CIE is below 20/50 cutoff)")

            target_grade = st.selectbox("Target Grade:", ["S / O (90%+)", "A (80%+)", "B (70%+)", "Pass (40%+)"])
            needed_see = calculate_see_needed(total_cie, target_grade)
            if needed_see <= 100:
                st.info(f"🎯 Target SEE Score needed: **{needed_see} / 100**")
            else:
                st.warning("Mathematically unreachable with current CIE.")

    # ----------------- TAB 2: SGPA CALCULATOR -----------------
    with tab2:
        st.header("🎯 Precise Semester SGPA Calculator")
        st.caption("Calculates your final SGPA based on all 6 subjects using VTU/NIE NEP grading rubrics.")

        st.subheader("Enter CIE (out of 50) and Estimated SEE (out of 100) for all subjects:")
        subject_inputs = []

        cols = st.columns(2)
        for idx, (s_name, s_info) in enumerate(SUBJECTS_CONFIG.items()):
            col_target = cols[idx % 2]
            with col_target:
                st.markdown(f"**{s_name}** `({s_info['credits']} Credits)`")
                c_cie, c_see = st.columns(2)
                cie_val = c_cie.number_input(f"CIE (50)", min_value=0.0, max_value=50.0, value=38.0, key=f"cie_{idx}")
                see_val = c_see.number_input(f"Expected SEE (100)", min_value=0.0, max_value=100.0, value=75.0, key=f"see_{idx}")
                subject_inputs.append({
                    "name": s_name,
                    "credits": s_info["credits"],
                    "cie_marks": cie_val,
                    "see_marks": see_val
                })
                st.markdown("---")

        sgpa_res = calculate_semester_sgpa(subject_inputs)

        st.subheader("📈 SGPA Calculation Result")
        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.metric("Projected SGPA", f"{sgpa_res['sgpa']} / 10.0")
            st.metric("Total Semester Credits", sgpa_res["total_credits"])

        with res_col2:
            st.dataframe(pd.DataFrame(sgpa_res["details"]), use_container_width=True, hide_index=True)

    # ----------------- TAB 3: SMART ASSIGNMENT TRACKER -----------------
    with tab3:
        st.header("📝 Smart Assignment Deadline Tracker")
        with st.expander("➕ Add New Assignment", expanded=False):
            with st.form("new_assignment_form"):
                subject_name = st.selectbox("Subject:", ALL_SUBJECT_NAMES)
                assignment_title = st.text_input("Assignment Name / Milestone:")
                due_date_val = st.date_input("Deadline Date:", min_value=date.today())
                if st.form_submit_button("Save Assignment"):
                    if assignment_title:
                        add_assignment(st.session_state.user, subject_name, assignment_title, str(due_date_val))
                        st.success("Assignment saved!")
                        refresh()
                    else:
                        st.warning("Please provide an assignment title.")

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
            st.dataframe(df[["ID", "Subject", "Assignment", "Deadline", "Status Indicator"]], use_container_width=True, hide_index=True)

            selected_ids = st.multiselect("Toggle Completion for Assignment IDs:", options=[item["id"] for item in raw_assignments])
            if st.button("Update Status"):
                for aid in selected_ids:
                    current_task = next(a for a in raw_assignments if a["id"] == aid)
                    toggle_assignment_completion(aid, 0 if current_task["is_completed"] else 1)
                st.success("Status updated!")
                refresh()
        else:
            st.info("No assignments recorded yet. Add your first assignment above!")