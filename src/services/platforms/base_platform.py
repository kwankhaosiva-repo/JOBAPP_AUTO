"""Base class for job platform integration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import urllib.parse
from src.models import CandidateProfile, SalaryExpectation


class BasePlatform(ABC):
    """Abstract base class representing a job board platform."""

    def __init__(
        self,
        platform_id: str,
        name: str,
        base_url: str,
        search_url_template: str,
        color: str,
        tag: str,
    ):
        self.platform_id = platform_id
        self.name = name
        self.base_url = base_url
        self.search_url_template = search_url_template
        self.color = color
        self.tag = tag

    def build_search_url(self, keywords: str, location: str = "Bangkok") -> str:
        """Constructs the search URL for the platform."""
        safe_kw = urllib.parse.quote(keywords.strip())
        safe_loc = urllib.parse.quote(location.strip())
        return self.search_url_template.format(keywords=safe_kw, location=safe_loc)

    def prepare_autofill_payload(
        self,
        candidate: CandidateProfile,
        salary_exp: SalaryExpectation,
        cover_letter: str = "",
        job_url: str = "",
    ) -> Dict[str, Any]:
        """Builds a ready-to-use form payload for clipboard and automated form fill."""
        return {
            "platform": self.name,
            "platform_id": self.platform_id,
            "job_url": job_url or self.base_url,
            "candidate_name_en": candidate.name,
            "candidate_name_th": candidate.name_th,
            "email": candidate.email,
            "phone": candidate.phone,
            "linkedin": candidate.linkedin_url,
            "github": candidate.github_url,
            "portfolio": candidate.portfolio_url,
            "education": candidate.education,
            "expected_salary_min": salary_exp.min_salary,
            "expected_salary_max": salary_exp.max_salary,
            "expected_salary_text_en": f"{salary_exp.min_salary:,} - {salary_exp.max_salary:,} {salary_exp.currency} (Negotiable)",
            "expected_salary_text_th": f"{salary_exp.min_salary:,} - {salary_exp.max_salary:,} บาท",
            "resume_pdf_path": candidate.resume_pdf_path,
            "resume_docx_path": candidate.resume_docx_path,
            "cover_letter": cover_letter,
        }

    @abstractmethod
    def get_instructions(self) -> str:
        """Platform-specific instructions for applying."""
        pass
