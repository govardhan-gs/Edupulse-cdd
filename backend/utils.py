import hashlib
from datetime import date, datetime

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def calculate_cie(test1: float, test2: float, lab_cie: float) -> dict:
    """
    Calculates CIE according to the NIE 2026-27 scheme:
    Total CIE (50) = Average of Tests (25) + Scaled Lab (25)
    """
    if not (0 <= test1 <= 25 and 0 <= test2 <= 25 and 0 <= lab_cie <= 50):
        raise ValueError("Marks out of permissible bounds.")
    
    test_avg = (test1 + test2) / 2.0
    lab_scaled = lab_cie / 2.0
    total_cie = round(test_avg + lab_scaled, 2)
    
    # 40% eligibility threshold (20 out of 50)
    is_eligible = total_cie >= 20.0
    
    return {
        "total_cie": total_cie,
        "is_eligible": is_eligible,
        "status_message": "Eligible for SEE" if is_eligible else "Not Eligible (CIE < 20/50)"
    }

def calculate_see_needed(total_cie: float, target_grade: str) -> float:
    """
    Calculates required marks in SEE (out of 100) to secure a target grade.
    Total = 50% CIE + 50% SEE
    """
    grade_cutoffs = {
        "S (90%+)": 90,
        "A (80%+)": 80,
        "B (70%+)": 70,
        "Pass (40%+)": 40
    }
    target_marks = grade_cutoffs.get(target_grade, 40)
    # Target formula: Total_CIE + (SEE / 2) >= target_marks
    needed_see = max(0.0, (target_marks - total_cie) * 2.0)
    return round(needed_see, 1)

def get_deadline_status(due_date_str: str, is_completed: bool, today: date = None) -> dict:
    """
    Compares current date with deadline and returns the 5 color-coded statuses
    specified on Page 3 of the synopsis:
    - Green: Completed
    - Red: Overdue
    - Orange: Due Today
    - Yellow: Due Soon (1-2 days)
    - Blue: Upcoming (>2 days)
    """
    if is_completed:
        return {"label": "Completed", "color": "green", "badge": "🟢 Completed"}
    
    if today is None:
        today = date.today()
        
    if isinstance(due_date_str, str):
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    else:
        due_date = due_date_str

    diff = (due_date - today).days

    if diff < 0:
        return {"label": "Overdue", "color": "red", "badge": f"🔴 Overdue ({abs(diff)}d late)"}
    elif diff == 0:
        return {"label": "Due Today", "color": "orange", "badge": "🟠 Due Today"}
    elif 1 <= diff <= 2:
        return {"label": "Due Soon", "color": "yellow", "badge": f"🟡 Due Soon ({diff}d left)"}
    else:
        return {"label": "Upcoming", "color": "blue", "badge": f"🔵 Upcoming ({diff}d left)"}

def calculate_sgpa(subjects: list) -> float:
    """
    Calculates SGPA based on list of dicts: [{'grade_point': 9, 'credit': 4}, ...]
    """
    total_credits = sum(s['credit'] for s in subjects)
    if total_credits == 0:
        return 0.0
    weighted_points = sum(s['grade_point'] * s['credit'] for s in subjects)
    return round(weighted_points / total_credits, 2)