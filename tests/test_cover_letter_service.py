"""Unit tests for the Cover Letter Generator service.
"""

from src.models import CoverLetterRequest
from src.services.cover_letter_service import CoverLetterService


def test_generate_fintech_cover_letter():
    service = CoverLetterService()
    req = CoverLetterRequest(
        company_name="Finnomena",
        job_position="Software Engineer (FinTech)",
        job_description="Seeking a software engineer to build financial microservices and trading data pipelines.",
        target_salary_min=40000,
        target_salary_max=45000,
    )
    letter = service.generate(req)

    assert "Finnomena" in letter
    assert "Chulalongkorn University" in letter
    assert "AI stock analysis" in letter or "FinTech" in letter
    assert "Kwankhao Sivasomboon" in letter
    assert "40,000 - 45,000 THB" in letter


def test_generate_computer_vision_cover_letter():
    service = CoverLetterService()
    req = CoverLetterRequest(
        company_name="SKYVIV Partner",
        job_position="Computer Vision Engineer",
        job_description="YOLO, video stream processing, RTSP, and edge inference.",
        target_salary_min=40000,
        target_salary_max=45000,
    )
    letter = service.generate(req)

    assert "SKYVIV" in letter
    assert "StaffLenz AI" in letter or "License Plate" in letter
    assert "Kwankhao Sivasomboon" in letter
