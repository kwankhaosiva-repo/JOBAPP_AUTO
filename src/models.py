"""Data models for candidate profile, salary evaluation, applications, and platforms.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SalaryExpectation(BaseModel):
    min_salary: int = Field(default=40000, description="Minimum expected salary in THB")
    max_salary: int = Field(default=45000, description="Maximum expected salary in THB")
    currency: str = Field(default="THB", description="Currency code")
    include_unspecified: bool = Field(
        default=True,
        description="Whether to include jobs where salary is not specified",
    )


class SalaryEvaluationResult(BaseModel):
    has_salary_tag: bool
    raw_salary_text: Optional[str] = None
    parsed_min: Optional[int] = None
    parsed_max: Optional[int] = None
    match_status: str  # MATCH, BELOW, ABOVE, UNSPECIFIED
    is_acceptable: bool
    explanation: str
    suggested_form_input: str
    thai_suggested_input: str


class CandidateProfile(BaseModel):
    name: str = "Kwankhao Sivasomboon"
    name_th: str = "ขวัญข้าว ศิวสมบูรณ์"
    email: str = "Kwankhaosiva@gmail.com"
    phone: str = "095-959-6921"
    linkedin_url: str = "https://linkedin.com/in/kwankhao-sivasomboon"
    github_url: str = "https://github.com/kwankhaosiva-repo"
    portfolio_url: str = "https://kwankhaosiva-repo.github.io/Kwankhao_WebCVPort"
    education: str = "B.Eng. Survey Engineering, Chulalongkorn University (2021-2025)"
    toeic_score: int = 580
    key_skills: List[str] = [
        "Python",
        "FastAPI",
        "Docker",
        "GCP (Cloud Run, Firestore)",
        "PyTorch",
        "OpenCV",
        "YOLOv11",
        "GenAI / RAG",
        "LangChain / LangGraph",
        "SQL",
    ]
    resume_pdf_path: str = ""
    resume_docx_path: str = ""
    about_me_summary: str = ""


class CoverLetterRequest(BaseModel):
    company_name: str
    job_position: str
    job_description: Optional[str] = ""
    target_salary_min: Optional[int] = 40000
    target_salary_max: Optional[int] = 45000
    focus_domain: Optional[str] = "ai_backend"  # ai_backend, fintech, vision, rag, general


class ApplicationRecord(BaseModel):
    id: Optional[int] = None
    company: str
    link: str = ""
    jd: str = ""
    employees: str = ""
    industry: str = ""
    job_position: str
    location: str = "Bangkok, Thailand"
    offer_salary: str = ""
    priority: str = "First"
    status: str = "Resume Sent"
    salary: str = "40,000 - 45,000 THB"
    hr_email: str = ""
    resume_sent: str = ""
    hr_contacted: str = ""
    interview_date: str = ""
    test_date: str = ""
    job_letter: str = ""
    notes: str = ""


class PlatformSearchRequest(BaseModel):
    platform: str
    keywords: str = "AI Engineer"
    location: str = "Bangkok"


class PlatformLaunchRequest(BaseModel):
    platform: str
    job_url: str
