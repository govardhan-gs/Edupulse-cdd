import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.models import init_db, get_user_assignments, add_assignment, toggle_assignment_completion
from backend.utils import calculate_cie_integrated, calculate_cie_theory, calculate_see_needed, calculate_semester_sgpa

init_db()

app = FastAPI(title="EduPulse API")

# Mount the frontend folder so CSS and JS are accessible
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_home():
    # Directly serves your index.html!
    return FileResponse("frontend/index.html")

# API: Calculate CIE
class CIERequest(BaseModel):
    test1: float
    test2: float
    lab_or_assign: float
    has_lab: bool

@app.post("/api/calculate-cie")
def api_cie(data: CIERequest):
    if data.has_lab:
        res = calculate_cie_integrated(data.test1, data.test2, data.lab_or_assign)
    else:
        res = calculate_cie_theory(data.test1, data.test2, data.lab_or_assign)
    return res

# API: Get Assignments for a student
@app.get("/api/assignments/{usn}")
def api_get_assignments(usn: str):
    return get_user_assignments(usn)