"""Cover letter generation service.

Synthesizes candidate background from aboutme.txt and example_coverletter.txt
with specific job descriptions, companies, and roles to create compelling,
authentic, and tailored cover letters.
"""

from typing import Optional
from src.models import CoverLetterRequest
from src.services.resume_service import ResumeService


class CoverLetterService:
    """Generates tailored cover letters mirroring Kwankhao's authentic voice and style."""

    def __init__(self, resume_service: Optional[ResumeService] = None):
        self.resume_service = resume_service or ResumeService()

    def generate(self, req: CoverLetterRequest) -> str:
        """Generates a professional cover letter tailored to the target role and company."""
        company = req.company_name.strip() or "Hiring Team"
        position = req.job_position.strip() or "Software/AI Engineer"
        jd = (req.job_description or "").lower()
        company_lower = company.lower()
        position_lower = position.lower()

        # Domain identification for tailored highlights
        is_fintech = any(
            w in jd or w in company_lower or w in position_lower
            for w in [
                "fintech",
                "finance",
                "bank",
                "stock",
                "trading",
                "investment",
                "scb",
                "kbank",
                "ttb",
                "tisco",
                "finnomena",
            ]
        )
        is_vision = any(
            w in jd or w in position_lower
            for w in ["vision", "cv", "image", "video", "camera", "yolo", "opencv", "detection"]
        )
        is_rag_genai = any(
            w in jd or w in position_lower
            for w in ["llm", "rag", "genai", "generative", "langchain", "langgraph", "vector", "nlp"]
        )
        is_product = any(
            w in jd or w in position_lower
            for w in ["product", "solution", "cross-functional", "business", "analyst"]
        )
        is_software = any(
            w in jd or w in position_lower
            for w in ["backend", "software", "api", "golang", "go", "developer", "system"]
        )

        # Paragraph 1: Introduction
        p1 = (
            f"Dear {company} Recruitment Team,\n\n"
            f"I am writing to express my strong interest in the {position} position at {company}. "
            "I graduated from Chulalongkorn University with a Bachelor’s degree in Survey Engineering "
            "and have transitioned into engineering through hands-on experience building and deploying "
            "AI-powered applications, backend services, REST APIs, and cloud solutions on GCP."
        )

        # Paragraph 2: Tailored Project Highlights
        project_sentences = []
        if is_fintech:
            project_sentences.append(
                "Having a deep personal interest in FinTech and capital markets, I built an AI stock analysis agent "
                "that integrates financial statements, technical price signals, and market news to classify trading sentiment. "
                "I actively follow earnings reports and market trends, allowing me to understand financial logic alongside technical architecture."
            )
        if is_vision:
            project_sentences.append(
                "In computer vision, I developed StaffLenz AI—an edge workplace analytics platform utilizing multi-camera RTSP feeds, "
                "YOLOv11-Pose, InsightFace embeddings, and OpenVINO FP16 inference, as well as an end-to-end Thai/Lao License Plate Recognition "
                "pipeline deployed on GCP Cloud Run achieving over 92% province accuracy."
            )
        if is_rag_genai:
            project_sentences.append(
                "In Generative AI and retrieval systems, I engineered a production Thai Legal RAG chatbot combining dense embeddings, "
                "BM25 keyword search, reciprocal rank fusion (RRF), and LangGraph agentic workflows deployed seamlessly on Google Cloud Run."
            )
        if is_software or not project_sentences:
            project_sentences.append(
                "My experience encompasses Python, FastAPI, Docker, CI/CD, and GCP (Cloud Run, Firestore, Secret Manager). "
                "I am accustomed to end-to-end engineering—from data flow design and database integration to unit testing, "
                "containerization, and maintaining production-oriented backend services."
            )

        p2 = (
            "My recent work centers on transforming practical business challenges into reliable, production-ready systems. "
            + " ".join(project_sentences)
        )

        # Paragraph 3: Value proposition & fit
        if is_product:
            p3 = (
                f"I am particularly drawn to {company} because this role bridges software development, data intelligence, "
                "and business problem-solving. I thrive on examining problems from multiple perspectives—evaluating technical trade-offs, "
                "designing intuitive workflows, and turning innovative concepts into tangible outcomes for end users."
            )
        elif is_fintech:
            p3 = (
                f"I am genuinely excited about the opportunity at {company} because it lies at the intersection of technology, "
                "data, and financial innovation. My motivation is to build systems that deliver concrete value, and I am eager to apply "
                "my analytical thinking and engineering foundation to help drive your team's initiatives."
            )
        else:
            p3 = (
                f"I am keen to contribute to {company} because I prioritize building maintainable, high-impact software "
                "that solves genuine problems. I am highly adaptable, comfortable learning new tech stacks quickly, "
                "and enjoy collaborating with cross-functional teams to iterate toward measurable results."
            )

        # Paragraph 4: Closing
        salary_note = ""
        if req.target_salary_min and req.target_salary_max:
            salary_note = (
                f" My expected salary range is {req.target_salary_min:,} - {req.target_salary_max:,} THB "
                "(open to discussion based on overall benefits and role structure)."
            )

        p4 = (
            "Although early in my professional career, I bring a solid engineering background, high autonomy, "
            f"and relentless curiosity.{salary_note} I welcome the opportunity to discuss how my skill set aligns with your team's goals."
        )

        signoff = (
            "Best regards,\n\n"
            "Kwankhao Sivasomboon\n"
            "Tel: (+66) 95-959-6921 | Email: Kwankhaosiva@gmail.com\n"
            "LinkedIn: linkedin.com/in/kwankhao-sivasomboon\n"
            "GitHub: github.com/kwankhaosiva-repo\n"
            "Portfolio: kwankhaosiva-repo.github.io/Kwankhao_WebCVPort"
        )

        return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}\n\n{signoff}"
