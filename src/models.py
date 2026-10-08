"""Data models for candidate profile, salary evaluation, compatibility scoring,
company presentation preparation, applications, and platforms.
"""

from typing import Dict, List, Optional
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
    focus_domain: Optional[str] = "ai_backend"


class CompatibilityRequest(BaseModel):
    company_name: str = ""
    job_position: str
    job_description: str = ""
    platform: str = "linkedin"
    link: str = ""
    min_salary: int = 40000
    max_salary: int = 45000
    llm_provider: Optional[str] = None  # auto, ollama, openai, heuristic


class CompatibilityResult(BaseModel):
    overall_score: int = Field(description="0-100 overall compatibility score")
    skill_match_score: int = Field(description="0-100 technical resume match score")
    goal_alignment_score: int = Field(description="0-100 career goal alignment with aboutme.txt")
    salary_fit_score: int = Field(description="0-100 salary compatibility score")
    is_compatible: bool = Field(description="True if overall_score meets threshold")
    recommended_status: str = Field(default="Considering")
    verdict_label: str
    matched_skills: List[str] = []
    growth_skills: List[str] = []
    matched_goals: List[str] = []
    reasoning: str
    suggested_domain: str = "ai_backend"
    engine_used: str = "smart_profile_matcher"


class PresentationSlide(BaseModel):
    slide_number: int
    title: str
    subtitle: str
    bullet_points: List[str]
    speaker_notes: str


class InterviewQA(BaseModel):
    question: str
    key_talking_points: str


class CompanyPrepRequest(BaseModel):
    record_id: Optional[int] = None
    company_name: str
    job_position: str
    industry: Optional[str] = ""
    job_description: Optional[str] = ""
    llm_provider: Optional[str] = None


class CompanyPrepReport(BaseModel):
    company_name: str
    job_position: str
    industry_category: str
    company_overview: str
    strategic_alignment: str
    key_focus_areas: List[str]
    research_links: List[Dict[str, str]]
    presentation_slides: List[PresentationSlide]
    interview_qas: List[InterviewQA]
    markdown_deck: str
    engine_used: str = "smart_prep_agent"


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
    status: str = "Considering"
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


class AutoDiscoverRequest(BaseModel):
    keywords: str = "AI Engineer, Machine Learning, Python"
    platforms: List[str] = Field(
        default_factory=lambda: ["linkedin", "jobsdb", "jobthai", "jobbkk", "jobtopgun", "workventure"]
    )
    location: str = "Bangkok"
    min_salary: int = 40000
    max_salary: int = 45000
    min_score_threshold: int = 65
    auto_save_considering: bool = True
    max_results: int = 12
    llm_provider: Optional[str] = None


class DiscoveredJobItem(BaseModel):
    company_name: str
    job_position: str
    platform: str
    platform_name: str
    location: str
    industry: str = ""
    salary_tag: str = "Not specified"
    link: str
    job_description: str
    source_type: str = "live_or_curated"
    evaluation: CompatibilityResult
    cover_letter: str
    saved_to_considering: bool = False
    already_in_history: bool = False
    record_id: Optional[int] = None


class AutoDiscoverResponse(BaseModel):
    total_found: int
    compatible_count: int
    newly_saved_count: int
    already_in_history_count: int
    engine_used: str
    requires_api_key: bool = False
    jobs: List[DiscoveredJobItem]


class LLMConfigUpdateRequest(BaseModel):
    provider: str = "auto"  # auto, heuristic, ollama, openai
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    compatibility_threshold: Optional[int] = None

