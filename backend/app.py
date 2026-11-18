import sys
import os

# 1. Ensure Python can always locate the project root and sibling modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st  # type: ignore[reportMissingImports]
import pandas as pd  # type: ignore[reportMissingImports]
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

# ----------------- CUSTOM HIGH-CONTRAST CSS FOR DROPDOWNS -----------------
# Fixes invisible text in Streamlit Dark Mode selectboxes
st.markdown("""
<style>
    /* Force dropdown selectbox text to be bright and visible */
    div[data-baseweb="select"] * {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid #3b82f6 !important;
    }
    /* Highlight the selected option tag */
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
    "Applied Mathematics-III (1BMAT301)": {"credits": 4, "has_lab": False},
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
        st.header("Single Subject CIE Evaluation")
        
        # 1. Subject Dropdown with Visible Confirmation
        sub_select = st.selectbox("Select Subject:", ALL_SUBJECT_NAMES, key="single_sub_select")
        cfg = SUBJECTS_CONFIG[sub_select]

        # VISIBLE SELECTION BADGE (Fixes the blank box issue)
        course_type = "🔬 Integrated with Lab" if cfg["has_lab"] else "📖 Theory Course"
        st.markdown(f"""
        <div class="selected-tag">
            👉 Selected Subject: <b>{sub_select}</b> | Credits: <b>{cfg['credits']}</b> | Type: <b>{course_type}</b>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Component Marks Input")
            t1 = st.slider("Test-1 Marks (Max 25):", 0.0, 25.0, 18.0, step=0.5, key="t1_single")
            t2 = st.slider("Test-2 Marks (Max 25):", 0.0, 25.0, 20.0, step=0.5, key="t2_single")

            if cfg["has_lab"]:
                st.caption("Formula: `(Test1 + Test2)/2 + Lab_CIE/2`")
                lab = st.slider("Lab CIE (Max 50):", 0.0, 50.0, 42.0, step=1.0, key="lab_single")
                cie_data = calculate_cie_integrated(t1, t2, lab)
            else:
                st.caption("Formula: `(Test1 + Test2)/2 + Assignment/2`")
                assign = st.slider("Assignment / Activity Marks (Max 50):", 0.0, 50.0, 40.0, step=1.0, key="assign_single")
                cie_data = calculate_cie_theory(t1, t2, assign)

        with col2:
            st.subheader("Eligibility & Prediction")
            total_cie = cie_data["total_cie"]
            st.metric("Total CIE Marks", f"{total_cie} / 50")

            if cie_data["is_eligible"]:
                st.success(f"✅ **Eligible for SEE in {sub_select}** (Satisfies ≥ 40% cutoff)")
            else:
                st.error(f"⚠️ **Ineligible for SEE in {sub_select}** (Below 20/50 cutoff threshold)")

            # 2. Target Grade Dropdown with Visible Confirmation
            target_grade = st.selectbox("Target Grade:", ["S / O (90%+)", "A (80%+)", "B (70%+)", "Pass (40%+)"], key="target_grade_select")
            st.markdown(f'<div class="selected-tag">🎯 Goal: <b>{target_grade}</b></div>', unsafe_allow_html=True)

            needed_see = calculate_see_needed(total_cie, target_grade)
            if needed_see <= 100:
                st.info(f"🎯 Target SEE Score needed in **{sub_select}**: **{needed_see} / 100**")
            else:
                st.warning("Mathematically unreachable with current CIE.")

    # -------------------------------------------------------------
    # TAB 2: DETAILED SEMESTER SGPA CALCULATOR
    # -------------------------------------------------------------
    with tab2:
        st.header("🎯 Precise Semester SGPA Calculator")
        st.caption("Calculates your final SGPA based on all 6 subjects using VTU/NIE NEP grading rubrics.")

        subject_inputs = []

        grid_cols = st.columns(2)
        for idx, (s_name, s_info) in enumerate(SUBJECTS_CONFIG.items()):
            col_target = grid_cols[idx % 2]
            
            with col_target:
                type_badge = "🔬 Integrated (with Lab)" if s_info["has_lab"] else "📖 Theory"
                st.markdown(f"### {s_name}")
                st.caption(f"**Credits:** `{s_info['credits']}` | **Type:** `{type_badge}`")

                c1, c2 = st.columns(2)
                t1_val = c1.number_input("Test-1 (25)", min_value=0.0, max_value=25.0, value=20.0, step=0.5, key=f"t1_{idx}")
                t2_val = c2.number_input("Test-2 (25)", min_value=0.0, max_value=25.0, value=20.0, step=0.5, key=f"t2_{idx}")

                c3, c4 = st.columns(2)
                if s_info["has_lab"]:
                    lab_val = c3.number_input("Lab CIE (50)", min_value=0.0, max_value=50.0, value=42.0, step=1.0, key=f"lab_{idx}")
                    cie_calculated = calculate_cie_integrated(t1_val, t2_val, lab_val)["total_cie"]
                else:
                    assign_val = c3.number_input("Assignment (50)", min_value=0.0, max_value=50.0, value=40.0, step=1.0, key=f"assign_{idx}")
                    cie_calculated = calculate_cie_theory(t1_val, t2_val, assign_val)["total_cie"]

                see_val = c4.number_input("Expected SEE (100)", min_value=0.0, max_value=100.0, value=75.0, step=1.0, key=f"see_{idx}")

                st.markdown(f"**Calculated Total CIE:** `{cie_calculated} / 50`")
                st.markdown("---")

                subject_inputs.append({
                    "name": s_name,
                    "credits": s_info["credits"],
                    "cie_marks": cie_calculated,
                    "see_marks": see_val
                })

        sgpa_res = calculate_semester_sgpa(subject_inputs)

        st.subheader("📈 Overall Semester Result & Grade Breakdown")
        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.metric("🎯 Projected SGPA", f"{sgpa_res['sgpa']} / 10.0")
            st.metric("Total Credits", sgpa_res["total_credits"])

        with res_col2:
            st.dataframe(pd.DataFrame(sgpa_res["details"]), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # TAB 3: SMART ASSIGNMENT DEADLINE TRACKER
    # -------------------------------------------------------------
    with tab3:
        st.header("📝 Smart Assignment Deadline Tracker")

        # 1. Create New Assignment
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
            # 2. Interactive Subject Filter
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

            # 3. Interactive Completion Status Selection
            st.markdown("### 🔄 Update Submission Status")
            
            selected_ids = st.multiselect(
                "Select Assignment IDs to toggle completion:",
                options=[item["id"] for item in raw_assignments],
                format_func=lambda x: f"ID {x}: {next(a['title'] for a in raw_assignments if a['id'] == x)}",
                key="id_multiselect"
            )

            # VISUAL CONFIRMATION: Show exact items selected
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