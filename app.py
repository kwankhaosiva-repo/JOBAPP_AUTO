"""FastAPI web application and REST API server for JOB_APP_AUTO.
"""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import (
    APPLICATION_PRIORITIES,
    APPLICATION_STATUSES,
    COMPATIBILITY_THRESHOLD,
    CSV_HISTORY_PATH,
    DEFAULT_MAX_SALARY,
    DEFAULT_MIN_SALARY,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    RESUME_DOCX_PATH,
    RESUME_PDF_PATH,
)
from src.models import (
    ApplicationRecord,
    CompanyPrepReport,
    CompanyPrepRequest,
    CompatibilityRequest,
    CompatibilityResult,
    CoverLetterRequest,
    PlatformLaunchRequest,
    PlatformSearchRequest,
    SalaryEvaluationResult,
    SalaryExpectation,
)
from src.services.agent_orchestrator import AgentOrchestrator
from src.services.company_prep_service import CompanyPrepService
from src.services.compatibility_service import CompatibilityService
from src.services.cover_letter_service import CoverLetterService
from src.services.history_tracker import HistoryTracker
from src.services.platforms.platform_manager import PlatformManager
from src.services.resume_service import ResumeService
from src.services.salary_matcher import SalaryMatcher
from src.services.scraper_service import ScraperService

app = FastAPI(
    title="JOB_APP_AUTO API",
    description="Semi-Automated Multi-Agent Job Application & Presentation Prep Suite",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services & Specialist Agents
resume_service = ResumeService()
salary_matcher = SalaryMatcher()
cover_letter_service = CoverLetterService(resume_service)
history_tracker = HistoryTracker()
platform_manager = PlatformManager()
scraper_service = ScraperService()
compatibility_service = CompatibilityService(resume_service, salary_matcher)
company_prep_service = CompanyPrepService()
orchestrator = AgentOrchestrator(
    compatibility_service=compatibility_service,
    cover_letter_service=cover_letter_service,
    company_prep_service=company_prep_service,
    history_tracker=history_tracker,
    platform_manager=platform_manager,
    scraper_service=scraper_service,
)

STATIC_DIR = Path(__file__).resolve().parent / "src" / "web" / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "src" / "web" / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Frontend & File Download Routes ---


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


@app.get("/api/history/export/csv")
async def export_history_csv():
    if not CSV_HISTORY_PATH.exists():
        raise HTTPException(status_code=404, detail="CSV file not found")
    return FileResponse(
        str(CSV_HISTORY_PATH),
        media_type="text/csv",
        filename="Job Application - Second Jobber.csv",
    )


@app.get("/api/history/export/excel")
async def export_history_excel():
    excel_path = history_tracker.export_to_excel()
    return FileResponse(
        str(excel_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Job Application - Second Jobber.xlsx",
    )


# --- API Routes ---


@app.get("/api/profile")
async def get_profile():
    profile = resume_service.get_candidate_profile()
    return profile.model_dump()


@app.get("/api/llm/status")
async def get_llm_status():
    return {
        "provider": LLM_PROVIDER,
        "ollama_base_url": OLLAMA_BASE_URL,
        "ollama_model": OLLAMA_MODEL,
        "openai_model": OPENAI_MODEL,
        "has_openai_key": bool(OPENAI_API_KEY),
        "compatibility_threshold": COMPATIBILITY_THRESHOLD,
    }


@app.get("/api/platforms")
async def get_platforms():
    return platform_manager.list_platforms()


@app.post("/api/platforms/search-url")
async def build_search_url(req: PlatformSearchRequest):
    plat = platform_manager.get_platform(req.platform)
    if not plat:
        raise HTTPException(status_code=404, detail=f"Platform {req.platform} not supported")
    url = plat.build_search_url(keywords=req.keywords, location=req.location)
    return {"platform": req.platform, "url": url}


@app.post("/api/platforms/launch")
async def launch_platform(req: PlatformLaunchRequest):
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
    exp = SalaryExpectation(
        min_salary=req.min_salary or DEFAULT_MIN_SALARY,
        max_salary=req.max_salary or DEFAULT_MAX_SALARY,
        include_unspecified=req.include_unspecified if req.include_unspecified is not None else True,
    )
    return salary_matcher.evaluate(
        salary_text_or_jd=req.salary_text_or_jd,
        job_title=req.job_title or "",
        expectation=exp,
    )


@app.post("/api/compatibility/evaluate", response_model=CompatibilityResult)
async def evaluate_compatibility(req: CompatibilityRequest):
    """Evaluates job compatibility with candidate resume, career goals, and salary."""
    return compatibility_service.evaluate(req)


class PipelineShortlistRequest(BaseModel):
    company_name: str
    job_position: str
    job_description: str = ""
    link: str = ""
    platform: str = "linkedin"
    industry: str = ""
    location: str = "Bangkok, Thailand"
    priority: str = "First"
    min_salary: int = DEFAULT_MIN_SALARY
    max_salary: int = DEFAULT_MAX_SALARY
    auto_save_if_compatible: bool = True
    force_save: bool = False
    llm_provider: Optional[str] = None


@app.post("/api/pipeline/shortlist")
async def run_shortlist_pipeline(req: PipelineShortlistRequest):
    """Runs the Multi-Agent Scout -> Evaluator -> Tailoring pipeline.
    Tags compatible jobs as 'Considering' in CSV & Excel.
    """
    return orchestrator.evaluate_and_shortlist(
        company_name=req.company_name,
        job_position=req.job_position,
        job_description=req.job_description,
        link=req.link,
        platform=req.platform,
        industry=req.industry,
        location=req.location,
        priority=req.priority,
        min_salary=req.min_salary,
        max_salary=req.max_salary,
        auto_save_if_compatible=req.auto_save_if_compatible,
        force_save=req.force_save,
        llm_provider=req.llm_provider,
    )


@app.post("/api/prep/generate", response_model=CompanyPrepReport)
async def generate_company_prep(req: CompanyPrepRequest):
    """Generates Company Intelligence & 5-Slide Presentation Deck for Submitted roles."""
    return orchestrator.prepare_presentation_for_submitted(
        record_id=req.record_id,
        company_name=req.company_name,
        job_position=req.job_position,
        industry=req.industry or "",
        job_description=req.job_description or "",
    )


@app.post("/api/cover-letter/generate")
async def generate_cover_letter(req: CoverLetterRequest):
    letter = cover_letter_service.generate(req)
    return {"cover_letter": letter, "company": req.company_name, "position": req.job_position}


@app.get("/api/history")
async def get_history(search: Optional[str] = None, status: Optional[str] = None):
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
        if status == "Submitted":
            records = [r for r in records if r.status in ("Submitted", "Resume Sent")]
        else:
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
    added = history_tracker.add_record(record)
    return {"success": True, "record": added.model_dump()}


class UpdateStatusRequest(BaseModel):
    record_id: int
    status: str
    notes: Optional[str] = None


@app.patch("/api/history/status")
async def update_status(req: UpdateStatusRequest):
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
    plat = platform_manager.get_platform(req.platform_id)
    if not plat:
        plat = platform_manager.get_platform("linkedin")

    candidate = resume_service.get_candidate_profile()
    salary_exp = SalaryExpectation(
        min_salary=req.min_salary or DEFAULT_MIN_SALARY,
        max_salary=req.max_salary or DEFAULT_MAX_SALARY,
    )
    return plat.prepare_autofill_payload(
        candidate=candidate,
        salary_exp=salary_exp,
        cover_letter=req.cover_letter or "",
        job_url=req.job_url or "",
    )
