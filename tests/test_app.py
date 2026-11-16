import pytest
from datetime import date, timedelta
from backend.utils import (
    calculate_cie,
    calculate_see_needed,
    get_deadline_status,
    hash_password,
    calculate_sgpa
)
from backend.models import (
    init_db,
    register_user,
    authenticate_user,
    add_assignment,
    get_user_assignments,
    toggle_assignment_completion
)

# ----------------- UTILS TESTS -----------------
def test_calculate_cie_eligible():
    # Test1: 20, Test2: 20 -> Avg = 20
    # Lab: 40 -> Scaled = 20 -> Total = 40.0
    res = calculate_cie(20, 20, 40)
    assert res["total_cie"] == 40.0
    assert res["is_eligible"] is True

def test_calculate_cie_ineligible():
    # Test1: 10, Test2: 10 -> Avg = 10
    # Lab: 18 -> Scaled = 9 -> Total = 19.0 (Below 20 cutoff)
    res = calculate_cie(10, 10, 18)
    assert res["total_cie"] == 19.0
    assert res["is_eligible"] is False

def test_calculate_cie_invalid_bounds():
    with pytest.raises(ValueError):
        calculate_cie(30, 20, 40)  # Test1 cannot exceed 25

def test_calculate_see_needed():
    # Total CIE is 35. For Grade A (80%), needed SEE = (80 - 35) * 2 = 90
    assert calculate_see_needed(35.0, "A (80%+)") == 90.0
    # Target already satisfied
    assert calculate_see_needed(45.0, "Pass (40%+)") == 0.0

def test_deadline_status_color_indicators():
    today = date(2026, 11, 10)
    
    # 1. Green - Completed
    assert get_deadline_status("2026-11-05", is_completed=True, today=today)["color"] == "green"
    
    # 2. Red - Overdue
    assert get_deadline_status("2026-11-08", is_completed=False, today=today)["color"] == "red"
    
    # 3. Orange - Due Today
    assert get_deadline_status("2026-11-10", is_completed=False, today=today)["color"] == "orange"
    
    # 4. Yellow - Due Soon (1-2 days)
    assert get_deadline_status("2026-11-12", is_completed=False, today=today)["color"] == "yellow"
    
    # 5. Blue - Upcoming (>2 days)
    assert get_deadline_status("2026-11-18", is_completed=False, today=today)["color"] == "blue"

def test_password_hashing():
    p1 = hash_password("secret123")
    p2 = hash_password("secret123")
    p3 = hash_password("different")
    assert p1 == p2
    assert p1 != p3

def test_calculate_sgpa():
    subjects = [
        {'grade_point': 9, 'credit': 4},
        {'grade_point': 8, 'credit': 4},
        {'grade_point': 10, 'credit': 2}
    ]
    # Total = (36 + 32 + 20) / 10 = 8.8
    assert calculate_sgpa(subjects) == 8.8

# ----------------- DATABASE TESTS -----------------
def test_database_crud(tmp_path):
    test_db = str(tmp_path / "test_edupulse.db")
    init_db(test_db)
    
    # Test registration and login
    assert register_user("4NI23CS001", "Govardhan", "password@123", db_path=test_db) is True
    assert register_user("4NI23CS001", "Duplicate", "pass", db_path=test_db) is False  # Duplicate USN
    assert authenticate_user("4NI23CS001", "password@123", db_path=test_db) is True
    assert authenticate_user("4NI23CS001", "wrongpass", db_path=test_db) is False
    
    # Test assignment management
    add_assignment("4NI23CS001", "CDD", "Lab 6 CI Workflow", "2026-11-15", db_path=test_db)
    tasks = get_user_assignments("4NI23CS001", db_path=test_db)
    assert len(tasks) == 1
    assert tasks[0]["is_completed"] == 0
    
    # Toggle complete
    toggle_assignment_completion(tasks[0]["id"], 1, db_path=test_db)
    updated_tasks = get_user_assignments("4NI23CS001", db_path=test_db)
    assert updated_tasks[0]["is_completed"] == 1