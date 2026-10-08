"""AI & Profile Job Compatibility Evaluation Service (Evaluator Agent).

Evaluates job postings against Kwankhao's Resume (PDF/DOCX), personal career
goals (aboutme.txt), and salary expectations. Supports pluggable backends:
- Localhost Ollama LLM (http://localhost:11434)
- Cloud OpenAI-compatible API (via OPENAI_API_KEY)
- Built-in Smart Profile & Goal Scorer (instant offline fallback)
"""

import json
import re
from typing import Dict, List, Optional, Tuple
import requests

from src.config import (
    COMPATIBILITY_THRESHOLD,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from src.models import (
    CompatibilityRequest,
    CompatibilityResult,
    SalaryExpectation,
)
from src.services.resume_service import ResumeService
from src.services.salary_matcher import SalaryMatcher


class CompatibilityService:
    """Evaluates job compatibility with candidate resume, skills, and career goals."""

    # Candidate core skills mapped to search keywords
    CANDIDATE_SKILL_MAP: Dict[str, List[str]] = {
        "Python": ["python"],
        "FastAPI": ["fastapi", "fast api"],
        "REST APIs": ["rest api", "restful", "api development", "apis", "backend"],
        "Docker": ["docker", "container"],
        "GCP / Cloud Run": ["gcp", "google cloud", "cloud run", "firestore", "cloud"],
        "PyTorch / Deep Learning": ["pytorch", "deep learning", "neural network"],
        "Computer Vision (YOLO/OpenCV)": ["computer vision", "opencv", "yolo", "image processing", "ocr", "video"],
        "GenAI & LLMs": ["genai", "generative ai", "llm", "large language model", "prompt", "ai agent"],
        "RAG & Vector Search": ["rag", "retrieval", "vector", "pinecone", "bm25", "embedding"],
        "LangChain / LangGraph": ["langchain", "langgraph"],
        "SQL & Databases": ["sql", "postgresql", "postgres", "mysql", "database"],
        "Machine Learning": ["machine learning", "scikit-learn", "ml", "classification", "prediction"],
        "Data Analysis (Pandas/NumPy)": ["pandas", "numpy", "data analysis", "data science", "analytics"],
        "CI/CD & Git": ["ci/cd", "git", "github", "cloud build", "devops"],
        "Automated Testing (Playwright)": ["playwright", "qa", "unit test", "testing", "pydantic"],
    }

    # Adjacent skills where candidate can highlight fast learning ability
    GROWTH_SKILL_MAP: Dict[str, List[str]] = {
        "Go (Golang)": ["golang", " go "],
        "Kubernetes": ["kubernetes", "k8s"],
        "AWS / Azure": ["aws", "azure"],
        "Kafka / Streaming": ["kafka", "rabbitmq", "streaming"],
        "TypeScript / React": ["typescript", "react", "node.js", "nodejs"],
        "Spark / Big Data": ["spark", "pyspark", "airflow", "databricks"],
    }

    # Career goals extracted from aboutme.txt
    CAREER_GOALS_MAP: Dict[str, List[str]] = {
        "AI Engineering & Production Systems": ["ai engineer", "ai", "machine learning", "ml", "model deployment", "inference"],
        "FinTech & Financial Analysis": ["fintech", "finance", "financial", "bank", "banking", "stock", "trading", "investment", "wealth", "insurance"],
        "Cloud & Scalable Backend": ["cloud", "backend", "microservice", "scalable", "api", "distributed", "software engineer"],
        "GenAI & Agentic Workflows": ["genai", "llm", "rag", "chatbot", "agent", "nlp"],
        "Bridging Tech & Business / Product": ["product", "solution", "business", "strategy", "stakeholder", "cross-functional", "end-to-end"],
    }

    def __init__(
        self,
        resume_service: Optional[ResumeService] = None,
        salary_matcher: Optional[SalaryMatcher] = None,
    ):
        self.resume_service = resume_service or ResumeService()
        self.salary_matcher = salary_matcher or SalaryMatcher()

    def evaluate(self, req: CompatibilityRequest) -> CompatibilityResult:
        """Evaluates job compatibility using configured AI provider or smart scorer."""
        provider = (req.llm_provider or LLM_PROVIDER or "auto").lower()

        # First compute deterministic baseline metrics
        baseline = self._evaluate_heuristic(req)

        if provider in ("ollama", "auto"):
            ollama_res = self._try_ollama_evaluation(req, baseline)
            if ollama_res is not None:
                return ollama_res

        if provider in ("openai", "auto") and OPENAI_API_KEY:
            openai_res = self._try_openai_evaluation(req, baseline)
            if openai_res is not None:
                return openai_res

        return baseline

    def _evaluate_heuristic(self, req: CompatibilityRequest) -> CompatibilityResult:
        """Deterministic profile, skill, career goal, and salary compatibility scorer."""
        combined_text = f"{req.company_name} {req.job_position} {req.job_description}".lower()
        title_lower = req.job_position.lower()

        # 1. Match technical skills from Resume
        matched_skills: List[str] = []
        for skill_label, keywords in self.CANDIDATE_SKILL_MAP.items():
            if any(kw in combined_text for kw in keywords):
                matched_skills.append(skill_label)

        growth_skills: List[str] = []
        for skill_label, keywords in self.GROWTH_SKILL_MAP.items():
            if any(kw in combined_text for kw in keywords):
                growth_skills.append(skill_label)

        # Calculate Skill Score
        # If JD is very short (just title), infer core skills from title
        if len(req.job_description.strip()) < 30:
            if any(k in title_lower for k in ["ai", "machine learning", "ml", "data", "vision", "llm"]):
                matched_skills = list(dict.fromkeys(matched_skills + ["Python", "PyTorch / Deep Learning", "GenAI & LLMs", "FastAPI"]))
            elif any(k in title_lower for k in ["software", "backend", "developer", "engineer"]):
                matched_skills = list(dict.fromkeys(matched_skills + ["Python", "FastAPI", "REST APIs", "Docker", "SQL & Databases"]))

        skill_count = len(matched_skills)
        if skill_count >= 6:
            skill_score = min(98, 82 + (skill_count - 6) * 3)
        elif skill_count >= 3:
            skill_score = 68 + (skill_count - 3) * 5
        elif skill_count >= 1:
            skill_score = 52 + skill_count * 7
        else:
            skill_score = 40

        # 2. Match Career Goals from aboutme.txt
        matched_goals: List[str] = []
        for goal_label, keywords in self.CAREER_GOALS_MAP.items():
            if any(kw in combined_text for kw in keywords):
                matched_goals.append(goal_label)

        goal_score = 55 + min(43, len(matched_goals) * 11)

        # Seniority check (Second Jobber: 1-3 yrs sweet spot)
        if any(w in title_lower for w in ["director", "vp", "head of", "principal", "chief"]):
            goal_score -= 30
            skill_score -= 20
        elif re.search(r"\b([7-9]|1\d)\+?\s*years", combined_text):
            goal_score -= 18
        elif any(w in title_lower for w in ["ai", "software", "backend", "data", "product", "machine learning", "fintech"]):
            goal_score = min(98, goal_score + 8)

        # 3. Salary Fit Score
        sal_exp = SalaryExpectation(min_salary=req.min_salary, max_salary=req.max_salary)
        sal_eval = self.salary_matcher.evaluate(
            req.job_description, job_title=req.job_position, expectation=sal_exp
        )
        if sal_eval.match_status == "MATCH":
            salary_score = 96
        elif sal_eval.match_status == "ABOVE":
            salary_score = 100
        elif sal_eval.match_status == "UNSPECIFIED":
            salary_score = 85
        else:
            salary_score = 35

        # 4. Determine Suggested Cover Letter Focus Domain
        suggested_domain = "ai_backend"
        if "FinTech & Financial Analysis" in matched_goals:
            suggested_domain = "fintech"
        elif "Computer Vision (YOLO/OpenCV)" in matched_skills:
            suggested_domain = "vision"
        elif "RAG & Vector Search" in matched_skills or "LangChain / LangGraph" in matched_skills:
            suggested_domain = "rag"
        elif "Bridging Tech & Business / Product" in matched_goals and "product" in title_lower:
            suggested_domain = "product"

        # 5. Weighted Overall Compatibility Score
        overall = int(round(skill_score * 0.45 + goal_score * 0.35 + salary_score * 0.20))
        overall = max(10, min(99, overall))

        is_compat = overall >= COMPATIBILITY_THRESHOLD and sal_eval.match_status != "BELOW"
        recommended_status = "Considering" if is_compat else "Draft"

        if overall >= 82:
            verdict = "Strong Match — Highly Recommended"
        elif overall >= COMPATIBILITY_THRESHOLD:
            verdict = "Good Fit — Recommended for Considering"
        elif overall >= 50:
            verdict = "Moderate Fit — Review Requirements"
        else:
            verdict = "Low Match — Below Target Threshold"

        skills_str = ", ".join(matched_skills[:5]) if matched_skills else "General Engineering"
        goals_str = ", ".join(matched_goals[:3]) if matched_goals else "Technical Growth"
        growth_note = (
            f" Opportunity to expand into {', '.join(growth_skills[:3])}."
            if growth_skills
            else ""
        )

        reasoning = (
            f"Matches {len(matched_skills)} core resume competencies ({skills_str}) and aligns with "
            f"career goals in {goals_str}. Salary status: {sal_eval.match_status} "
            f"(target {req.min_salary:,}-{req.max_salary:,} THB).{growth_note}"
        )

        return CompatibilityResult(
            overall_score=overall,
            skill_match_score=max(0, min(100, skill_score)),
            goal_alignment_score=max(0, min(100, goal_score)),
            salary_fit_score=salary_score,
            is_compatible=is_compat,
            recommended_status=recommended_status,
            verdict_label=verdict,
            matched_skills=matched_skills,
            growth_skills=growth_skills,
            matched_goals=matched_goals,
            reasoning=reasoning,
            suggested_domain=suggested_domain,
            engine_used="smart_profile_matcher",
        )

    def _build_llm_prompt(self, req: CompatibilityRequest, baseline: CompatibilityResult) -> str:
        about_me = self.resume_service.read_about_me()
        return (
            "You are an expert technical career advisor evaluating job compatibility for Kwankhao Sivasomboon.\n"
            f"Candidate Profile & Goals:\n{about_me}\n\n"
            "Candidate Key Skills: Python, FastAPI, Docker, GCP (Cloud Run, Firestore, Secret Manager), "
            "PyTorch, YOLOv11, OpenCV, InsightFace, OpenVINO, GenAI/RAG, LangChain, LangGraph, BM25, SQL.\n"
            f"Target Salary: {req.min_salary:,} - {req.max_salary:,} THB.\n\n"
            f"Target Job:\nCompany: {req.company_name}\nRole: {req.job_position}\nJD: {req.job_description[:2000]}\n\n"
            "Return ONLY a JSON object with keys: "
            '{"overall_score": int (0-100), "skill_match_score": int, "goal_alignment_score": int, '
            '"reasoning": "2-sentence concise analysis of fit with resume and career goals"}'
        )

    def _try_ollama_evaluation(
        self, req: CompatibilityRequest, baseline: CompatibilityResult
    ) -> Optional[CompatibilityResult]:
        """Attempts evaluation via local Ollama server if reachable."""
        try:
            prompt = self._build_llm_prompt(req, baseline)
            resp = requests.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=8,
            )
            if resp.status_code == 200:
                raw_response = resp.json().get("response", "{}")
                parsed = json.loads(raw_response)
                overall = int(parsed.get("overall_score", baseline.overall_score))
                is_compat = overall >= COMPATIBILITY_THRESHOLD
                return baseline.model_copy(
                    update={
                        "overall_score": overall,
                        "skill_match_score": int(parsed.get("skill_match_score", baseline.skill_match_score)),
                        "goal_alignment_score": int(parsed.get("goal_alignment_score", baseline.goal_alignment_score)),
                        "is_compatible": is_compat,
                        "recommended_status": "Considering" if is_compat else "Draft",
                        "reasoning": parsed.get("reasoning", baseline.reasoning),
                        "engine_used": f"ollama ({OLLAMA_MODEL})",
                    }
                )
        except Exception:
            pass
        return None

    def _try_openai_evaluation(
        self, req: CompatibilityRequest, baseline: CompatibilityResult
    ) -> Optional[CompatibilityResult]:
        """Attempts evaluation via OpenAI-compatible API when OPENAI_API_KEY is configured."""
        if not OPENAI_API_KEY:
            return None
        try:
            prompt = self._build_llm_prompt(req, baseline)
            resp = requests.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                },
                timeout=12,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                overall = int(parsed.get("overall_score", baseline.overall_score))
                is_compat = overall >= COMPATIBILITY_THRESHOLD
                return baseline.model_copy(
                    update={
                        "overall_score": overall,
                        "skill_match_score": int(parsed.get("skill_match_score", baseline.skill_match_score)),
                        "goal_alignment_score": int(parsed.get("goal_alignment_score", baseline.goal_alignment_score)),
                        "is_compatible": is_compat,
                        "recommended_status": "Considering" if is_compat else "Draft",
                        "reasoning": parsed.get("reasoning", baseline.reasoning),
                        "engine_used": f"openai ({OPENAI_MODEL})",
                    }
                )
        except Exception:
            pass
        return None
