"""FastAPI web application and REST API server for JOB_APP_AUTO.
"""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import (
    APPLICATION_PRIORITIES,
    APPLICATION_STATUSES,
    DEFAULT_CURRENCY,
    DEFAULT_MAX_SALARY,
    DEFAULT_MIN_SALARY,
    RESUME_DOCX_PATH,
    RESUME_PDF_PATH,
)
from src.models import (
    ApplicationRecord,
    CoverLetterRequest,
    PlatformLaunchRequest,
    PlatformSearchRequest,
    SalaryEvaluationResult,
    SalaryExpectation,
)
from src.services.cover_letter_service import CoverLetterService
from src.services.history_tracker import HistoryTracker
from src.services.platforms.platform_manager import PlatformManager
from src.services.resume_service import ResumeService
from src.services.salary_matcher import SalaryMatcher
from src.services.scraper_service import ScraperService

app = FastAPI(
    title="JOB_APP_AUTO API",
    description="Automated Job Application Engine & Application Tracker",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
resume_service = ResumeService()
salary_matcher = SalaryMatcher()
cover_letter_service = CoverLetterService(resume_service)
history_tracker = HistoryTracker()
platform_manager = PlatformManager()
scraper_service = ScraperService()

# Mount Static Files
STATIC_DIR = Path(__file__).resolve().parent / "src" / "web" / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "src" / "web" / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Frontend Routes ---


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    return index_file.read_text(encoding="utf-8")


@app.get("/resume/pdf")
async def download_resume_pdf():
    if not RESUME_PDF_PATH.exists():
        raise HTTPException(status_code=404, detail="Resume PDF not found")
    return FileResponse(
        str(RESUME_PDF_PATH),
        media_type="application/pdf",
        filename="Kwankhao_Sivasomboon_Resume.pdf",
    )


@app.get("/resume/docx")
async def download_resume_docx():
    if not RESUME_DOCX_PATH.exists():
        raise HTTPException(status_code=404, detail="Resume DOCX not found")
    return FileResponse(
        str(RESUME_DOCX_PATH),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="Kwankhao_Sivasomboon_Resume.docx",
    )


# --- API Routes ---


@app.get("/api/profile")
async def get_profile():
    """Returns candidate profile details."""
    profile = resume_service.get_candidate_profile()
    return profile.model_dump()


@app.get("/api/platforms")
async def get_platforms():
    """Returns list of supported platforms and quick links."""
    return platform_manager.list_platforms()


@app.post("/api/platforms/search-url")
async def build_search_url(req: PlatformSearchRequest):
    """Generates direct search URL for a given platform."""
    plat = platform_manager.get_platform(req.platform)
    if not plat:
        raise HTTPException(status_code=404, detail=f"Platform {req.platform} not supported")
    url = plat.build_search_url(keywords=req.keywords, location=req.location)
    return {"platform": req.platform, "url": url}


@app.post("/api/platforms/launch")
async def launch_platform(req: PlatformLaunchRequest):
    """Opens job posting or search URL in the user's browser."""
    success = platform_manager.launch_browser_url(req.job_url)
    return {"success": success, "url": req.job_url}


class SalaryCheckRequest(BaseModel):
    salary_text_or_jd: str
    job_title: Optional[str] = ""
    min_salary: Optional[int] = DEFAULT_MIN_SALARY
    max_salary: Optional[int] = DEFAULT_MAX_SALARY
    include_unspecified: Optional[bool] = True


@app.post("/api/salary/evaluate", response_model=SalaryEvaluationResult)
async def evaluate_salary(req: SalaryCheckRequest):
    """Parses and evaluates salary against user's target expectations."""
    exp = SalaryExpectation(
        min_salary=req.min_salary or DEFAULT_MIN_SALARY,
        max_salary=req.max_salary or DEFAULT_MAX_SALARY,
        include_unspecified=req.include_unspecified if req.include_unspecified is not None else True,
    )
    result = salary_matcher.evaluate(
        salary_text_or_jd=req.salary_text_or_jd,
        job_title=req.job_title or "",
        expectation=exp,
    )
    return result


@app.post("/api/cover-letter/generate")
async def generate_cover_letter(req: CoverLetterRequest):
    """Generates a tailored, authentic cover letter matching the candidate profile."""
    letter = cover_letter_service.generate(req)
    return {"cover_letter": letter, "company": req.company_name, "position": req.job_position}


@app.get("/api/history")
async def get_history(search: Optional[str] = None, status: Optional[str] = None):
    """Returns application records from the CSV file."""
    records = history_tracker.load_records()
    if search:
        s = search.lower()
        records = [
            r
            for r in records
            if s in r.company.lower()
            or s in r.job_position.lower()
            or s in r.notes.lower()
        ]
    if status and status != "All":
        records = [r for r in records if r.status == status]

    stats = history_tracker.get_summary_stats()
    return {
        "records": [r.model_dump() for r in records],
        "stats": stats,
        "available_statuses": APPLICATION_STATUSES,
        "available_priorities": APPLICATION_PRIORITIES,
    }


@app.post("/api/history")
async def add_history_record(record: ApplicationRecord):
    """Adds a new application entry to docs/Job Application - Second Jobber.csv."""
    added = history_tracker.add_record(record)
    return {"success": True, "record": added.model_dump()}


class UpdateStatusRequest(BaseModel):
    record_id: int
    status: str
    notes: Optional[str] = None


@app.patch("/api/history/status")
async def update_status(req: UpdateStatusRequest):
    """Updates an existing application status in the CSV."""
    success = history_tracker.update_record_status(
        record_id=req.record_id, new_status=req.status, notes=req.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"success": True, "record_id": req.record_id, "new_status": req.status}


class AutofillPayloadRequest(BaseModel):
    platform_id: str
    job_url: Optional[str] = ""
    cover_letter: Optional[str] = ""
    min_salary: Optional[int] = DEFAULT_MIN_SALARY
    max_salary: Optional[int] = DEFAULT_MAX_SALARY


@app.post("/api/autofill-payload")
async def get_autofill_payload(req: AutofillPayloadRequest):
    """Generates ready-to-copy application field payloads."""
    plat = platform_manager.get_platform(req.platform_id)
    if not plat:
        plat = platform_manager.get_platform("linkedin")

    candidate = resume_service.get_candidate_profile()
    salary_exp = SalaryExpectation(
        min_salary=req.min_salary or DEFAULT_MIN_SALARY,
        max_salary=req.max_salary or DEFAULT_MAX_SALARY,
    )
    payload = plat.prepare_autofill_payload(
        candidate=candidate,
        salary_exp=salary_exp,
        cover_letter=req.cover_letter or "",
        job_url=req.job_url or "",
    )
    return payload
