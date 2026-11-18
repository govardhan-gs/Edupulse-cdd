import hashlib
from datetime import date, datetime

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def calculate_cie_detailed(test1: float, test2: float, quiz: float, lab_or_assign: float, is_lab: bool = False) -> dict:
    """
    Calculates CIE according to NIE 100 -> 50 scaling:
    - Test-1: Max 25
    - Test-2: Max 25
    - Quiz: Max 20
    - Lab / Assignment: Max 30
    Total CIE (100) -> Scaled to CIE (50)

    Eligibility Conditions for SEE:
    1. Condition 1: Test1 + Test2 >= 20 marks
    2. Condition 2: Total CIE (out of 100) >= 40 marks (40% threshold)
    """
    if not (0 <= test1 <= 25 and 0 <= test2 <= 25 and 0 <= quiz <= 20 and 0 <= lab_or_assign <= 30):
        raise ValueError("Marks out of permissible limits.")

    tests_total = test1 + test2
    cie_100 = round(test1 + test2 + quiz + lab_or_assign, 2)
    cie_50 = round(cie_100 / 2.0, 2)

    cond1_passed = tests_total >= 20.0
    cond2_passed = cie_100 >= 40.0
    is_eligible = cond1_passed and cond2_passed

    reasons = []
    if not cond1_passed:
        reasons.append(f"Condition 1 Failed: Internal Tests sum is {tests_total}/50 (Need at least 20 marks).")
    if not cond2_passed:
        reasons.append(f"Condition 2 Failed: Overall CIE is {cie_100}/100 (Need at least 40% / 40 marks).")

    return {
        "tests_total": tests_total,
        "cie_100": cie_100,
        "cie_50": cie_50,
        "cond1_passed": cond1_passed,
        "cond2_passed": cond2_passed,
        "is_eligible": is_eligible,
        "failure_reasons": reasons
    }

def calculate_see_needed(cie_50: float, target_grade: str) -> float:
    """Calculates required SEE score (out of 100) to secure target grade."""
    grade_cutoffs = {
        "S / O (90%+)": 90,
        "A (80%+)": 80,
        "B (70%+)": 70,
        "Pass (40%+)": 40
    }
    target_marks = grade_cutoffs.get(target_grade, 40)
    # Total = cie_50 + (see_100 / 2) >= target_marks
    needed_see = max(0.0, (target_marks - cie_50) * 2.0)
    return round(needed_see, 1)

def marks_to_grade_point(total_marks_100: float) -> tuple:
    """Converts combined 100 marks (50 CIE + 50 SEE) to Grade Points (VTU/NIE NEP Scheme)."""
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
    Calculates precise SGPA:
    CIE (50) + SEE scaled (see_100 / 2) = Final (100)
    SGPA = Sum(Credit * Grade_Point) / Sum(Credits)
    """
    total_credits = 0
    total_credit_points = 0
    detailed_results = []

    for item in subject_data_list:
        cie_50 = item["cie_50"]
        see_100 = item["see_100"]
        credits = item["credits"]

        see_50 = see_100 / 2.0
        total_100 = min(100.0, round(cie_50 + see_50, 1))
        gp, letter = marks_to_grade_point(total_100)

        total_credits += credits
        total_credit_points += (credits * gp)

        detailed_results.append({
            "Subject": item["name"],
            "Credits": credits,
            "CIE (50)": cie_50,
            "SEE Scaled (50)": see_50,
            "Total (100)": total_100,
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