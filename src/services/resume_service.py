"""Resume and candidate profile service.

Loads candidate information, extracts text from resume PDF/DOCX,
reads background story from aboutme.txt, and provides structured profiles.
"""

from pathlib import Path
from typing import Optional
import pymupdf
from src.config import (
    ABOUT_ME_PATH,
    EXAMPLE_COVER_LETTER_PATH,
    RESUME_DOCX_PATH,
    RESUME_PDF_PATH,
)
from src.models import CandidateProfile


class ResumeService:
    """Manages candidate profile data and resume documents."""

    def __init__(
        self,
        resume_pdf_path: Path = RESUME_PDF_PATH,
        resume_docx_path: Path = RESUME_DOCX_PATH,
        about_me_path: Path = ABOUT_ME_PATH,
        example_letter_path: Path = EXAMPLE_COVER_LETTER_PATH,
    ):
        self.resume_pdf_path = resume_pdf_path
        self.resume_docx_path = resume_docx_path
        self.about_me_path = about_me_path
        self.example_letter_path = example_letter_path

    def extract_resume_text(self) -> str:
        """Extracts text content from the candidate's PDF resume."""
        if not self.resume_pdf_path.exists():
            return ""

        try:
            doc = pymupdf.open(str(self.resume_pdf_path))
            full_text = []
            for page in doc:
                full_text.append(page.get_text())
            doc.close()
            return "\n".join(full_text).strip()
        except Exception as e:
            return f"Error reading PDF: {e}"

    def read_about_me(self) -> str:
        """Reads candidate personal background and motivation narrative."""
        if not self.about_me_path.exists():
            return ""
        try:
            return self.about_me_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            return f"Error reading aboutme.txt: {e}"

    def read_example_cover_letter(self) -> str:
        """Reads the candidate's reference cover letter."""
        if not self.example_letter_path.exists():
            return ""
        try:
            return self.example_letter_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            return f"Error reading example_coverletter.txt: {e}"

    def get_candidate_profile(self) -> CandidateProfile:
        """Constructs and returns the comprehensive candidate profile."""
        about_me = self.read_about_me()

        return CandidateProfile(
            name="Kwankhao Sivasomboon",
            name_th="ขวัญข้าว ศิวสมบูรณ์",
            email="Kwankhaosiva@gmail.com",
            phone="095-959-6921",
            linkedin_url="https://linkedin.com/in/kwankhao-sivasomboon",
            github_url="https://github.com/kwankhaosiva-repo",
            portfolio_url="https://kwankhaosiva-repo.github.io/Kwankhao_WebCVPort",
            education="B.Eng. Survey Engineering, Chulalongkorn University (2021-2025)",
            toeic_score=580,
            key_skills=[
                "Python",
                "FastAPI",
                "Docker",
                "GCP (Cloud Run, Secret Manager, Firestore)",
                "PyTorch",
                "OpenCV",
                "YOLOv11",
                "InsightFace",
                "GenAI & RAG",
                "LangChain & LangGraph",
                "Vector Search (Pinecone, BM25)",
                "SQL & PostgreSQL",
            ],
            resume_pdf_path=str(self.resume_pdf_path.resolve()),
            resume_docx_path=str(self.resume_docx_path.resolve()),
            about_me_summary=about_me,
        )
