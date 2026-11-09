import streamlit as st
import pandas as pd
from datetime import date
import sqlite3, hashlib

# ---------- DB helpers ----------
DB_PATH = "data/edupulse.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        usn TEXT PRIMARY KEY,
        name TEXT,
        pwd_hash TEXT
    );
    CREATE TABLE IF NOT EXISTS cie_scores(
        usn TEXT,
        test1 INTEGER,
        test2 INTEGER,
        lab INTEGER,
        FOREIGN KEY(usn) REFERENCES users(usn)
    );
    CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usn TEXT,
        subject TEXT,
        title TEXT,
        due DATE,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY(usn) REFERENCES users(usn)
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- Authentication ----------
def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def signup(usn, name, pwd):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users(usn,name,pwd_hash) VALUES (?,?,?)",
            (usn, name, hash_pwd(pwd)),
        )
        conn.commit()
    finally:
        conn.close()

def login(usn, pwd):
    conn = get_conn()
    cur = conn.execute(
        "SELECT pwd_hash FROM users WHERE usn=?",
        (usn,),
    )
    row = cur.fetchone()
    conn.close()
    return row and row["pwd_hash"] == hash_pwd(pwd)

# ---------- CIE calculation ----------
def calculate_cie(test1, test2, lab):
    test_avg = (test1 + test2) / 2          # out of 25
    lab_scaled = lab / 2                    # 50 → 25
    return round(test_avg + lab_scaled, 1)  # total out of 50

# ---------- Streamlit UI ----------
st.set_page_config(page_title="EduPulse", layout="wide")
st.title("⚡ EduPulse – CIE & Assignment Dashboard")

if "user" not in st.session_state:
    page = st.radio("Select", ["Login", "Sign‑up"])
    if page == "Login":
        usn = st.text_input("USN")
        pwd = st.text_input("Password", type="password")
        if st.button("Log in"):
            if login(usn, pwd):
                st.session_state.user = usn
                st.success("Logged in")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    else:  # Sign‑up
        usn = st.text_input("USN")
        name = st.text_input("Full name")
        pwd = st.text_input("Password", type="password")
        if st.button("Create account"):
            try:
                signup(usn, name, pwd)
                st.success("Account created – you can now log in")
            except Exception as e:
                st.error(f"Error: {e}")

else:
    # ------ Main dashboard ----------
    usn = st.session_state.user
    tab_cie, tab_assign = st.tabs(["CIE Analyzer", "Assignment Tracker"])

    # ---- CIE Analyzer ----
    with tab_cie:
        st.subheader("Enter your internal marks")
        col1, col2, col3 = st.columns(3)
        with col1: test1 = st.slider("Test‑1 (0‑25)", 0, 25, 0)
        with col2: test2 = st.slider("Test‑2 (0‑25)", 0, 25, 0)
        with col3: lab   = st.slider("Lab CIE (0‑50)", 0, 50, 0)

        total_cie = calculate_cie(test1, test2, lab)
        st.metric("Total CIE (out of 50)", total_cie)

        if total_cie >= 20:
            st.success("✅ Eligible for SEE")
        else:
            st.error("⚠️ Not eligible (need ≥ 20)")

        target = st.selectbox("Target final grade", ["S (90%+)", "A (80%+)", "B (70%+)", "Pass (40%+)"])
        # Convert target to required SEE marks (simple 50 % weighting)
        target_percent = {"S (90%+)":90, "A (80%+)":80, "B (70%+)":70, "Pass (40%+)":40}[target]
        need_see = max(0, (target_percent - total_cie) * 2)   # because SEE is 100 pts
        st.info(f"🔢 You need **{need_see:.0f} / 100** in SEE to achieve **{target}**")

        # Persist CIE scores (optional)
        if st.button("Save CIE"):
            conn = get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO cie_scores(usn,test1,test2,lab) VALUES (?,?,?,?)",
                (usn, test1, test2, lab)
            )
            conn.commit()
            conn.close()
            st.success("CIE saved")

    # ---- Assignment Tracker ----
    with tab_assign:
        st.subheader("Your Assignments")
        # Add new assignment
        with st.expander("➕ Add Assignment"):
            subj   = st.text_input("Subject name")
            title  = st.text_input("Assignment title")
            due    = st.date_input("Due date", min_value=date.today())
            if st.button("Add"):
                conn = get_conn()
                conn.execute(
                    "INSERT INTO assignments(usn,subject,title,due) VALUES (?,?,?,?)",
                    (usn, subj, title, due.isoformat())
                )
                conn.commit()
                conn.close()
                st.success("Assignment added")

        # Show table with status badges
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT id,subject,title,due,completed FROM assignments WHERE usn=?",
            conn,
            params=(usn,)
        )
        conn.close()

        if not df.empty:
            df["Due"] = pd.to_datetime(df["Due"])
            today = pd.Timestamp(date.today())
            def badge(row):
                if row["completed"]: return "✅ Completed"
                diff = (row["Due"] - today).days
                if diff < 0:   return "🔴 Overdue"
                if diff == 0:  return "🚨 Due Today"
                if diff <= 2:  return "🟠 Due Soon"
                return "🟢 Upcoming"
            df["Status"] = df.apply(badge, axis=1)
            st.dataframe(df[["subject","title","Due","Status"]])

            # Mark as done
            ids = st.multiselect("Select assignments to mark as completed", df["id"])
            if st.button("Mark Completed"):
                conn = get_conn()
                conn.executemany(
                    "UPDATE assignments SET completed=1 WHERE id=?",
                    [(i,) for i in ids]
                )
                conn.commit()
                conn.close()
                st.success("Updated")
        else:
            st.info("No assignments yet – add one above.")