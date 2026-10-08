"""Central configuration module for JOB_APP_AUTO.

Manages application paths, salary expectations, supported platforms,
and tracking settings.
"""

from pathlib import Path
from typing import Dict, List

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

# Document File Paths
RESUME_PDF_PATH = DOCS_DIR / "Kwankhao_Sivasomboon_Resume.pdf"
RESUME_DOCX_PATH = DOCS_DIR / "Kwankhao_Sivasomboon_Resume.docx"
ABOUT_ME_PATH = DOCS_DIR / "aboutme.txt"
EXAMPLE_COVER_LETTER_PATH = DOCS_DIR / "example_coverletter.txt"
CSV_HISTORY_PATH = DOCS_DIR / "Job Application - Second Jobber.csv"

# Salary Defaults
DEFAULT_MIN_SALARY = 40000
DEFAULT_MAX_SALARY = 45000
DEFAULT_CURRENCY = "THB"

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

# Common application statuses
APPLICATION_STATUSES: List[str] = [
    "Draft",
    "Resume Sent",
    "HR Contacted",
    "Interview Scheduled",
    "Technical Test",
    "Offer Received",
    "Not Pass?",
    "Withdrawn",
]

# Priorities
APPLICATION_PRIORITIES: List[str] = ["First", "Second", "Third", "Backup"]
