import sys
import os

# Ensure Python can always locate root and sibling modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
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
        calculate_cie_detailed,
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
        calculate_cie_detailed,
        calculate_see_needed,
        calculate_semester_sgpa,
        get_deadline_status
    )

init_db()

st.set_page_config(page_title="EduPulse - Student Dashboard", page_icon="⚡", layout="wide")

# High-contrast CSS for dropdown selectbox visibility
st.markdown("""
<style>
    div[data-baseweb="select"] * {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid #3b82f6 !important;
    }
    .selected-tag {
        background-color: #1e3a8a;
        color: #60a5fa !important;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin-top: 4px;
        margin-bottom: 12px;
        border: 1px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SEMESTER 3 COURSE DEFINITION -----------------
SUBJECTS_CONFIG = {
    # 1. Theory Course (Updated to 3 credits)
    "Applied Mathematics-III (1BMAT301)": {"credits": 3, "has_lab": False},

    # 2. Lab Integrated Course
    "DDCO (1BCS302)": {"credits": 4, "has_lab": True},

    # 3. Theory Course (CDD)
    "Collaborative development and devops (1BCS303)": {"credits": 4, "has_lab": False},

    # 4. Lab Integrated Course
    "Data structures and application (1BCS304)": {"credits": 4, "has_lab": True},

    # 5. Theory Course
    "Object Oriented programming Java (1BCS305)": {"credits": 3, "has_lab": False},

    # 6. Lab Integrated Course
    "Data Analytics and Visualization": {"credits": 3, "has_lab": False}
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
    st.markdown("Please log in with your university credentials (e.g. `4NI23CS001` / `password123`).")
    
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

# ----------------- MAIN DASHBOARD -----------------
else:
    st.sidebar.title("⚡ EduPulse")
    st.sidebar.markdown(f"👤 Logged in as: **`{st.session_state.user}`**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        refresh()

    st.title("🎓 Student Academic Performance & Smart Assignment Tracker")

    tab1, tab2, tab3 = st.tabs([
        "📊 Module 1: Single Subject CIE Analyser",
        "🎯 Module 2: Semester SGPA Calculator",
        "📝 Module 3: Smart Assignment Deadline Tracker"
    ])

    # -------------------------------------------------------------
    # TAB 1: SINGLE SUBJECT CIE ANALYSER
    # -------------------------------------------------------------
    with tab1:
        st.header("Single Subject CIE Evaluation & SEE Eligibility Check")
        sub_select = st.selectbox("Select Subject:", ALL_SUBJECT_NAMES, key="single_sub_select")
        cfg = SUBJECTS_CONFIG[sub_select]

        course_type = "🔬 Integrated with Lab" if cfg["has_lab"] else "📖 Theory Course"
        st.markdown(f"""
        <div class="selected-tag">
            👉 Selected: <b>{sub_select}</b> | Credits: <b>{cfg['credits']}</b> | Type: <b>{course_type}</b>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Component Marks Input")
            st.caption("CIE Total (100) = Test-1 (25) + Test-2 (25) + Quiz (20) + Lab/Assignment (30)")

            t1 = st.slider("Test-1 Marks (Max 25):", 0.0, 25.0, 18.0, step=0.5, key="t1_single")
            t2 = st.slider("Test-2 Marks (Max 25):", 0.0, 25.0, 19.0, step=0.5, key="t2_single")
            quiz = st.slider("Single Quiz Marks (Max 20):", 0.0, 20.0, 15.0, step=0.5, key="quiz_single")

            if cfg["has_lab"]:
                lab_assign = st.slider("Lab Continuous Evaluation (Max 30):", 0.0, 30.0, 25.0, step=0.5, key="lab_single")
            else:
                lab_assign = st.slider("Assignment Evaluation (Max 30):", 0.0, 30.0, 25.0, step=0.5, key="assign_single")

            cie_data = calculate_cie_detailed(t1, t2, quiz, lab_assign, is_lab=cfg["has_lab"])

        with col2:
            st.subheader("CIE Scores & Eligibility Verification")
            
            c_score1, c_score2 = st.columns(2)
            c_score1.metric("Total CIE (Out of 100)", f"{cie_data['cie_100']} / 100")
            c_score2.metric("Scaled CIE (Out of 50)", f"{cie_data['cie_50']} / 50")

            st.markdown("#### 📋 SEE Eligibility Status:")

            # Condition 1 Check
            if cie_data["cond1_passed"]:
                st.success(f"✅ **Condition 1 Met:** Test-1 + Test-2 = **{cie_data['tests_total']} / 50** (Minimum 20 required).")
            else:
                st.error(f"❌ **Condition 1 Failed:** Test-1 + Test-2 = **{cie_data['tests_total']} / 50** (Must score ≥ 20 marks across tests).")

            # Condition 2 Check
            if cie_data["cond2_passed"]:
                st.success(f"✅ **Condition 2 Met:** Overall CIE = **{cie_data['cie_100']} / 100** ({cie_data['cie_50']} / 50, satisfies 40% cutoff).")
            else:
                st.error(f"❌ **Condition 2 Failed:** Overall CIE = **{cie_data['cie_100']} / 100** (Must score ≥ 40% across all components).")

            # Final Eligibility Outcome
            if cie_data["is_eligible"]:
                st.success(f"🎉 **Eligible to appear for Semester End Examination (SEE) in {sub_select}!**")
            else:
                st.error(f"🚫 **Barred from SEE in {sub_select} until eligibility criteria are met!**")

            st.markdown("---")
            st.subheader("🎯 SEE Target Predictor")
            target_grade = st.selectbox("Target Grade:", ["S / O (90%+)", "A (80%+)", "B (70%+)", "Pass (40%+)"], key="target_grade_select")
            st.markdown(f'<div class="selected-tag">🎯 Goal: <b>{target_grade}</b></div>', unsafe_allow_html=True)

            needed_see = calculate_see_needed(cie_data["cie_50"], target_grade)
            if needed_see <= 100:
                st.info(f"To achieve **{target_grade}**, you must score at least **{needed_see} / 100** in SEE (which scales to **{needed_see/2:.1f}/50**).")
            else:
                st.warning("Mathematically unreachable: Current CIE requires more than 100/100 in SEE.")

    # -------------------------------------------------------------
    # TAB 2: DETAILED SEMESTER SGPA CALCULATOR
    # -------------------------------------------------------------
    with tab2:
        st.header("🎯 Precise Semester SGPA Calculator")
        st.caption("Marks Breakdown: Test-1 (25) + Test-2 (25) + Quiz (20) + Lab/Assignment (30) = Total 100 (Scaled down to 50). SEE 100 marks scaled down to 50.")

        subject_inputs = []

        grid_cols = st.columns(2)
        for idx, (s_name, s_info) in enumerate(SUBJECTS_CONFIG.items()):
            col_target = grid_cols[idx % 2]
            
            with col_target:
                type_badge = "🔬 Lab Subject" if s_info["has_lab"] else "📖 Non-Lab Subject"
                st.markdown(f"### {s_name}")
                st.caption(f"**Credits:** `{s_info['credits']}` | **Type:** `{type_badge}`")

                c1, c2, c3 = st.columns(3)
                t1_val = c1.number_input("Test-1 (25)", min_value=0.0, max_value=25.0, value=20.0, step=0.5, key=f"t1_{idx}")
                t2_val = c2.number_input("Test-2 (25)", min_value=0.0, max_value=25.0, value=20.0, step=0.5, key=f"t2_{idx}")
                quiz_val = c3.number_input("Quiz (20)", min_value=0.0, max_value=20.0, value=16.0, step=0.5, key=f"quiz_{idx}")

                c4, c5 = st.columns(2)
                if s_info["has_lab"]:
                    lab_or_assign_val = c4.number_input("Lab Marks (30)", min_value=0.0, max_value=30.0, value=25.0, step=0.5, key=f"lab_{idx}")
                else:
                    lab_or_assign_val = c4.number_input("Assignment (30)", min_value=0.0, max_value=30.0, value=25.0, step=0.5, key=f"assign_{idx}")

                see_val = c5.number_input("Expected SEE (100)", min_value=0.0, max_value=100.0, value=80.0, step=1.0, key=f"see_{idx}")

                # Calculate CIE 100 -> 50
                cie_calc = calculate_cie_detailed(t1_val, t2_val, quiz_val, lab_or_assign_val, is_lab=s_info["has_lab"])
                see_scaled_50 = see_val / 2.0
                course_final_100 = cie_calc["cie_50"] + see_scaled_50

                st.markdown(f"📊 **CIE (100):** `{cie_calc['cie_100']}` &nbsp;|&nbsp; **CIE (50):** `{cie_calc['cie_50']}` &nbsp;|&nbsp; **SEE (50):** `{see_scaled_50}` &nbsp;|&nbsp; **Final:** `{course_final_100}/100`")
                st.markdown("---")

                subject_inputs.append({
                    "name": s_name,
                    "credits": s_info["credits"],
                    "cie_50": cie_calc["cie_50"],
                    "see_100": see_val
                })

        # Calculate Overall SGPA
        sgpa_res = calculate_semester_sgpa(subject_inputs)

        st.subheader("📈 Overall Semester SGPA & Grade Sheet")
        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.metric("🎯 Projected SGPA", f"{sgpa_res['sgpa']} / 10.0")
            st.metric("Total Semester Credits", sgpa_res["total_credits"])

        with res_col2:
            st.dataframe(pd.DataFrame(sgpa_res["details"]), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # TAB 3: SMART ASSIGNMENT DEADLINE TRACKER
    # -------------------------------------------------------------
    with tab3:
        st.header("📝 Smart Assignment Deadline Tracker")

        with st.expander("➕ Add New Assignment", expanded=False):
            with st.form("new_assignment_form"):
                subject_name = st.selectbox("Select Subject for Assignment:", ALL_SUBJECT_NAMES, key="new_assign_sub")
                st.caption(f"📌 Task will be filed under: **{subject_name}**")
                
                assignment_title = st.text_input("Assignment Name / Milestone:", placeholder="e.g. Exp 6: GitHub Actions CI")
                due_date_val = st.date_input("Deadline Date:", min_value=date.today())
                
                if st.form_submit_button("Save Assignment"):
                    if assignment_title:
                        add_assignment(st.session_state.user, subject_name, assignment_title, str(due_date_val))
                        st.success(f"Assignment '{assignment_title}' added for {subject_name}!")
                        refresh()
                    else:
                        st.warning("Please provide an assignment title.")

        raw_assignments = get_user_assignments(st.session_state.user)
        
        if raw_assignments:
            st.markdown("### 📋 Assignment List")
            filter_sub = st.selectbox("🔍 Filter Table by Subject:", ["All Subjects"] + ALL_SUBJECT_NAMES, key="table_filter")
            st.markdown(f'<div class="selected-tag">🔍 Active Filter: <b>{filter_sub}</b></div>', unsafe_allow_html=True)

            if filter_sub == "All Subjects":
                filtered_assignments = raw_assignments
            else:
                filtered_assignments = [a for a in raw_assignments if a["subject"] == filter_sub]

            display_list = []
            for item in filtered_assignments:
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

            st.markdown("### 🔄 Update Submission Status")
            selected_ids = st.multiselect(
                "Select Assignment IDs to toggle completion:",
                options=[item["id"] for item in raw_assignments],
                format_func=lambda x: f"ID {x}: {next(a['title'] for a in raw_assignments if a['id'] == x)}",
                key="id_multiselect"
            )

            if selected_ids:
                selected_titles = [f"ID {aid} ({next(a['title'] for a in raw_assignments if a['id'] == aid)})" for aid in selected_ids]
                st.markdown(f'<div class="selected-tag">🎯 Selected for Update: <b>{", ".join(selected_titles)}</b></div>', unsafe_allow_html=True)

            if st.button("Toggle Status (Completed / Incomplete)", disabled=(len(selected_ids) == 0)):
                for aid in selected_ids:
                    current_task = next(a for a in raw_assignments if a["id"] == aid)
                    toggle_assignment_completion(aid, 0 if current_task["is_completed"] else 1)
                st.success("Assignment status updated successfully!")
                refresh()
        else:
            st.info("No assignments recorded yet. Add your first assignment above!")