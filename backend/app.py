import streamlit as st
import pandas as pd
from datetime import date
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

init_db()

st.set_page_config(page_title="EduPulse - Student Dashboard", layout="wide")
st.title("⚡ EduPulse: Academic Performance & Assignment Tracker")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    mode = st.sidebar.radio("Navigation", ["Login", "Sign Up"])
    usn = st.sidebar.text_input("USN (e.g. 4NI23CS001)")
    pwd = st.sidebar.text_input("Password", type="password")
    
    if mode == "Login" and st.sidebar.button("Login"):
        if authenticate_user(usn, pwd):
            st.session_state.user = usn.upper()
            st.rerun()
        else:
            st.sidebar.error("Invalid USN or Password")
            
    elif mode == "Sign Up":
        name = st.sidebar.text_input("Full Name")
        if st.sidebar.button("Create Account"):
            if register_user(usn, name, pwd):
                st.sidebar.success("Account created! Please log in.")
            else:
                st.sidebar.error("USN already exists.")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    tab1, tab2 = st.tabs(["📊 Module 1: CIE Performance Analyser", "📝 Module 2: Smart Assignment Tracker"])

    with tab1:
        st.subheader("CIE Marks Evaluation (NIE 2026-27 Scheme)")
        c1, c2, c3 = st.columns(3)
        t1 = c1.slider("Test-1 Marks (0-25)", 0, 25, 18)
        t2 = c2.slider("Test-2 Marks (0-25)", 0, 25, 20)
        lab = c3.slider("Lab CIE (0-50)", 0, 50, 42)

        cie_res = calculate_cie(t1, t2, lab)
        st.metric("Total CIE Marks", f"{cie_res['total_cie']} / 50")
        
        if cie_res["is_eligible"]:
            st.success("✅ Eligible for Semester End Examination (SEE)!")
        else:
            st.error("⚠️ Ineligible: CIE is below the minimum 20/50 threshold.")

        target = st.selectbox("Target Grade Goal:", ["S (90%+)", "A (80%+)", "B (70%+)", "Pass (40%+)"])
        see_req = calculate_see_needed(cie_res["total_cie"], target)
        st.info(f"🎯 Target SEE Score needed: **{see_req} / 100**")

    with tab2:
        st.subheader("Multi-Subject Assignment Deadline Tracker")
        with st.expander("➕ Add New Assignment"):
            sub = st.selectbox("Select Subject:", [
                "Collaborative Dev & DevOps (1BCS303)",
                "Operating Systems",
                "Database Management Systems",
                "Discrete Mathematical Structures"
            ])
            title = st.text_input("Assignment Name:")
            due = st.date_input("Deadline Date:", min_value=date.today())
            if st.button("Save Assignment"):
                add_assignment(st.session_state.user, sub, title, str(due))
                st.success("Assignment saved!")
                st.rerun()

        assignments = get_user_assignments(st.session_state.user)
        if assignments:
            formatted = []
            for a in assignments:
                st_info = get_deadline_status(a["due_date"], bool(a["is_completed"]))
                formatted.append({
                    "ID": a["id"],
                    "Subject": a["subject"],
                    "Assignment": a["title"],
                    "Due Date": a["due_date"],
                    "Status Indicator": st_info["badge"],
                    "Completed": bool(a["is_completed"])
                })
            df = pd.DataFrame(formatted)
            st.dataframe(df[["Subject", "Assignment", "Due Date", "Status Indicator"]], use_container_width=True)

            to_toggle = st.multiselect("Toggle Completion for Assignment IDs:", [a["id"] for a in assignments])
            if st.button("Update Status"):
                for aid in to_toggle:
                    curr = next(a for a in assignments if a["id"] == aid)
                    toggle_assignment_completion(aid, 0 if curr["is_completed"] else 1)
                st.rerun()
        else:
            st.info("No assignments recorded yet. Add your first task above!")
