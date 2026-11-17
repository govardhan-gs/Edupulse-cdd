import hashlib
from datetime import date, datetime

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def calculate_cie_integrated(test1: float, test2: float, lab_cie: float) -> dict:
    """
    For Integrated Subjects (Test1 + Test2 + Lab):
    Total CIE (50) = Test Avg (25) + Scaled Lab (25)
    """
    if not (0 <= test1 <= 25 and 0 <= test2 <= 25 and 0 <= lab_cie <= 50):
        raise ValueError("Marks out of permissible bounds.")
    
    test_avg = (test1 + test2) / 2.0
    lab_scaled = lab_cie / 2.0
    total_cie = round(test_avg + lab_scaled, 2)
    is_eligible = total_cie >= 20.0
    
    return {
        "total_cie": total_cie,
        "is_eligible": is_eligible,
        "status_message": "Eligible for SEE" if is_eligible else "Not Eligible (CIE < 20/50)"
    }

def calculate_cie_theory(test1: float, test2: float, assignment: float = 0.0) -> dict:
    """
    For Theory-Only Subjects:
    Total CIE (50) = (Test1 + Test2) or Test Avg (25) + Assignment (25)
    """
    total_cie = round(((test1 + test2) / 2.0) + (assignment / 2.0 if assignment > 0 else (test1 + test2) / 2.0), 2)
    is_eligible = total_cie >= 20.0
    return {
        "total_cie": total_cie,
        "is_eligible": is_eligible,
        "status_message": "Eligible for SEE" if is_eligible else "Not Eligible (CIE < 20/50)"
    }

def calculate_see_needed(total_cie: float, target_grade: str) -> float:
    grade_cutoffs = {
        "S / O (90%+)": 90,
        "A (80%+)": 80,
        "B (70%+)": 70,
        "Pass (40%+)": 40
    }
    target_marks = grade_cutoffs.get(target_grade, 40)
    needed_see = max(0.0, (target_marks - total_cie) * 2.0)
    return round(needed_see, 1)

def marks_to_grade_point(total_marks_100: float) -> tuple:
    """Converts total 100 marks (50 CIE + 50 SEE) to Grade & Grade Points (VTU/NIE NEP Scheme)."""
    if total_marks_100 >= 90: return (10, "O (Outstanding)")
    elif total_marks_100 >= 80: return (9, "A+ (Excellent)")
    elif total_marks_100 >= 70: return (8, "A (Very Good)")
    elif total_marks_100 >= 60: return (7, "B+ (Good)")
    elif total_marks_100 >= 50: return (6, "B (Above Average)")
    elif total_marks_100 >= 45: return (5, "C (Average)")
    elif total_marks_100 >= 40: return (4, "P (Pass)")
    else: return (0, "F (Fail)")

def calculate_semester_sgpa(subject_data_list: list) -> dict:
    """
    Calculates precise SGPA = Sum(Credit * Grade_Point) / Sum(Credits)
    """
    total_credits = 0
    total_credit_points = 0
    detailed_results = []

    for item in subject_data_list:
        cie_50 = item["cie_marks"]
        see_100 = item["see_marks"]
        credits = item["credits"]

        # Final score out of 100: 50% CIE + 50% SEE
        total_100 = min(100.0, cie_50 + (see_100 / 2.0))
        gp, letter = marks_to_grade_point(total_100)
        
        total_credits += credits
        total_credit_points += (credits * gp)

        detailed_results.append({
            "Subject": item["name"],
            "Credits": credits,
            "CIE (50)": cie_50,
            "Est. SEE (100)": see_100,
            "Total (100)": round(total_100, 1),
            "Grade Point": gp,
            "Grade": letter
        })

    sgpa = round(total_credit_points / total_credits, 2) if total_credits > 0 else 0.0
    return {
        "sgpa": sgpa,
        "total_credits": total_credits,
        "details": detailed_results
    }

def get_deadline_status(due_date_str: str, is_completed: bool, today: date = None) -> dict:
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