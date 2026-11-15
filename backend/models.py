import sqlite3
import os
from backend.utils import hash_password

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "edupulse.db")

def get_connection(db_path=DB_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    """Initializes SQLite database tables."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        usn TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS cie_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usn TEXT,
        subject TEXT NOT NULL,
        test1 REAL,
        test2 REAL,
        lab_cie REAL,
        total_cie REAL,
        FOREIGN KEY(usn) REFERENCES users(usn)
    );

    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usn TEXT,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        due_date DATE NOT NULL,
        is_completed INTEGER DEFAULT 0,
        FOREIGN KEY(usn) REFERENCES users(usn)
    );
    """)
    conn.commit()
    conn.close()

# ---------- USER OPERATIONS ----------
def register_user(usn: str, name: str, password: str, db_path=DB_PATH) -> bool:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO users (usn, name, password_hash) VALUES (?, ?, ?)",
            (usn.strip().upper(), name.strip(), hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(usn: str, password: str, db_path=DB_PATH) -> bool:
    conn = get_connection(db_path)
    cur = conn.execute("SELECT password_hash FROM users WHERE usn = ?", (usn.strip().upper(),))
    row = cur.fetchone()
    conn.close()
    if row and row["password_hash"] == hash_password(password):
        return True
    return False

# ---------- ASSIGNMENT OPERATIONS ----------
def add_assignment(usn: str, subject: str, title: str, due_date: str, db_path=DB_PATH):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO assignments (usn, subject, title, due_date, is_completed) VALUES (?, ?, ?, ?, 0)",
        (usn.strip().upper(), subject, title, due_date)
    )
    conn.commit()
    conn.close()

def get_user_assignments(usn: str, db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.execute("SELECT * FROM assignments WHERE usn = ? ORDER BY due_date ASC", (usn.strip().upper(),))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def toggle_assignment_completion(assignment_id: int, is_completed: int, db_path=DB_PATH):
    conn = get_connection(db_path)
    conn.execute("UPDATE assignments SET is_completed = ? WHERE id = ?", (is_completed, assignment_id))
    conn.commit()
    conn.close()

