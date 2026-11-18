import pytest
from datetime import date
from backend.utils import (
    calculate_cie_detailed,
    calculate_see_needed,
    marks_to_grade_point,
    calculate_semester_sgpa,
    get_deadline_status,
    hash_password
)
from backend.models import (
    init_db,
    register_user,
    authenticate_user,
    add_assignment,
    get_user_assignments,
    toggle_assignment_completion
)

# ----------------- CIE & ELIGIBILITY TESTS -----------------
def test_cie_both_conditions_passed():
    # T1=12, T2=12 (Tests sum=24 >= 20 -> Cond1 Pass)
    # Quiz=15, Lab=25 -> Total CIE = 12+12+15+25 = 64/100 (>= 40 -> Cond2 Pass)
    # Scaled CIE = 32.0 / 50
    res = calculate_cie_detailed(12, 12, 15, 25, is_lab=True)
    assert res["tests_total"] == 24.0
    assert res["cie_100"] == 64.0
    assert res["cie_50"] == 32.0
    assert res["cond1_passed"] is True
    assert res["cond2_passed"] is True
    assert res["is_eligible"] is True

def test_cie_condition1_failed_tests_under_20():
    # T1=8, T2=8 (Tests sum=16 < 20 -> Cond1 Fail!)
    # Quiz=20, Lab=30 -> Total CIE = 8+8+20+30 = 66/100 (>= 40 -> Cond2 Pass)
    # Even though overall is 66%, student is ineligible because tests < 20!
    res = calculate_cie_detailed(8, 8, 20, 30, is_lab=True)
    assert res["cond1_passed"] is False
    assert res["cond2_passed"] is True
    assert res["is_eligible"] is False

def test_cie_condition2_failed_overall_under_40():
    # T1=10, T2=10 (Tests sum=20 >= 20 -> Cond1 Pass)
    # Quiz=5, Lab=10 -> Total CIE = 10+10+5+10 = 35/100 (< 40 -> Cond2 Fail!)
    res = calculate_cie_detailed(10, 10, 5, 10, is_lab=False)
    assert res["cond1_passed"] is True
    assert res["cond2_passed"] is False
    assert res["is_eligible"] is False

def test_calculate_see_needed():
    # CIE_50 is 35. For Grade A (80%), needed SEE = (80 - 35) * 2 = 90
    assert calculate_see_needed(35.0, "A (80%+)") == 90.0

def test_marks_to_grade_point():
    assert marks_to_grade_point(92)[0] == 10
    assert marks_to_grade_point(85)[0] == 9
    assert marks_to_grade_point(38)[0] == 0  # Fail

def test_calculate_semester_sgpa():
    # Total credits = 3 + 4 = 7
    sample_data = [
        {"name": "Maths", "credits": 3, "cie_50": 40.0, "see_100": 80.0},  # Total = 40 + 40 = 80 -> GP 9
        {"name": "DDCO", "credits": 4, "cie_50": 45.0, "see_100": 90.0},   # Total = 45 + 45 = 90 -> GP 10
    ]
    # Credit points = (3 * 9) + (4 * 10) = 27 + 40 = 67
    # SGPA = 67 / 7 = 9.57
    res = calculate_semester_sgpa(sample_data)
    assert res["sgpa"] == 9.57
    assert res["total_credits"] == 7

def test_deadline_status():
    today = date(2026, 11, 10)
    assert get_deadline_status("2026-11-05", True, today)["color"] == "green"
    assert get_deadline_status("2026-11-08", False, today)["color"] == "red"
    assert get_deadline_status("2026-11-10", False, today)["color"] == "orange"
    assert get_deadline_status("2026-11-12", False, today)["color"] == "yellow"
    assert get_deadline_status("2026-11-18", False, today)["color"] == "blue"

def test_database_crud(tmp_path):
    test_db = str(tmp_path / "test.db")
    init_db(test_db)
    assert register_user("4NI23CS001", "Govardhan", "pass123", db_path=test_db) is True
    assert authenticate_user("4NI23CS001", "pass123", db_path=test_db) is True
    add_assignment("4NI23CS001", "CDD", "Task 1", "2026-11-20", db_path=test_db)
    tasks = get_user_assignments("4NI23CS001", db_path=test_db)
    assert len(tasks) == 1
    toggle_assignment_completion(tasks[0]["id"], 1, db_path=test_db)
    assert get_user_assignments("4NI23CS001", db_path=test_db)[0]["is_completed"] == 1