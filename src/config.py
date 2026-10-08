"""Central configuration module for JOB_APP_AUTO.

Manages application paths, salary expectations, supported platforms,
AI/LLM backend configuration, and tracking settings.
"""

import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

# Document File Paths
RESUME_PDF_PATH = DOCS_DIR / "Kwankhao_Sivasomboon_Resume.pdf"
RESUME_DOCX_PATH = DOCS_DIR / "Kwankhao_Sivasomboon_Resume.docx"
ABOUT_ME_PATH = DOCS_DIR / "aboutme.txt"
EXAMPLE_COVER_LETTER_PATH = DOCS_DIR / "example_coverletter.txt"
CSV_HISTORY_PATH = DOCS_DIR / "Job Application - Second Jobber.csv"
EXCEL_HISTORY_PATH = DOCS_DIR / "Job Application - Second Jobber.xlsx"

# Salary Defaults
DEFAULT_MIN_SALARY = 40000
DEFAULT_MAX_SALARY = 45000
DEFAULT_CURRENCY = "THB"

# AI & LLM Compatibility Engine Configuration (Pluggable: Ollama / OpenAI / Built-in Scorer)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")  # auto, ollama, openai, heuristic
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
COMPATIBILITY_THRESHOLD = int(os.getenv("COMPATIBILITY_THRESHOLD", "65"))

# Job Application CSV Headers (Matching exact schema in docs/Job Application - Second Jobber.csv)
CSV_HEADERS = [
    "Company",
    "Link",
    "JD",
    "Employees",
    "Industry",
    "Job Position",
    "Location",
    "Offer Salary",
    "Priority",
    "Status",
    "Salary",
    "HR Email",
    "Resume Sent",
    "HR Contacted",
    "Interview date",
    "Test date",
    "Job Letter",
    "Notes",
]

# Supported Platforms Configuration
PLATFORMS: Dict[str, Dict[str, str]] = {
    "linkedin": {
        "name": "LinkedIn",
        "base_url": "https://www.linkedin.com/jobs",
        "search_url_template": "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}",
        "color": "#0a66c2",
        "tag": "Global & Thai Tech",
    },
    "jobsdb": {
        "name": "JobsDB (SEEK)",
        "base_url": "https://th.jobsdb.com",
        "search_url_template": "https://th.jobsdb.com/th/search-jobs/{keywords}-in-{location}/1",
        "color": "#ff6000",
        "tag": "Top Thai Corporate",
    },
    "jobthai": {
        "name": "JobThai",
        "base_url": "https://www.jobthai.com",
        "search_url_template": "https://www.jobthai.com/th/jobs?keyword={keywords}",
        "color": "#e11d48",
        "tag": "High Volume Thai",
    },
    "jobbkk": {
        "name": "JobBKK",
        "base_url": "https://www.jobbkk.com",
        "search_url_template": "https://www.jobbkk.com/jobs/search?keyword={keywords}",
        "color": "#2563eb",
        "tag": "Bangkok Metro",
    },
    "jobtopgun": {
        "name": "JobTopGun",
        "base_url": "https://www.jobtopgun.com",
        "search_url_template": "https://www.jobtopgun.com/search?keyword={keywords}",
        "color": "#059669",
        "tag": "Thai Professionals",
    },
    "workventure": {
        "name": "WorkVenture",
        "base_url": "https://www.workventure.com",
        "search_url_template": "https://www.workventure.com/search?keywords={keywords}",
        "color": "#7c3aed",
        "tag": "Modern Tech Companies",
    },
}

# Semi-Auto Application Statuses (Considering -> Submitted -> Interview)
APPLICATION_STATUSES: List[str] = [
    "Considering",
    "Submitted",
    "Resume Sent",
    "HR Contacted",
    "Interview Scheduled",
    "Technical Test",
    "Offer Received",
    "Not Pass?",
    "Draft",
    "Withdrawn",
]

# Priorities
APPLICATION_PRIORITIES: List[str] = ["First", "Second", "Third", "Backup"]
