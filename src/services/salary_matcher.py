"""Salary evaluation and parsing service.

Detects salary tags from job descriptions or salary strings in both Thai and English.
Provides intelligent handling for postings that do not include a price tag,
which represents the majority of tech roles on Thai job platforms.
"""

import re
from typing import Optional, Tuple
from src.models import SalaryEvaluationResult, SalaryExpectation


class SalaryMatcher:
    """Evaluates job salaries against candidate expectations and handles unpriced roles."""

    def __init__(self, default_expectation: Optional[SalaryExpectation] = None):
        self.expectation = default_expectation or SalaryExpectation()

        # Regular expressions for Thai & English salary patterns
        self.range_patterns = [
            # 40,000 - 45,000 or 40000 - 45000 THB/บาท
            re.compile(r"(\d{1,3}(?:,\d{3})+|\d{4,6})\s*(?:-|to|–|—|ถึง)\s*(\d{1,3}(?:,\d{3})+|\d{4,6})\s*(?:thb|baht|บาท|k|บ\.)?", re.IGNORECASE),
            # 40k - 50k or 40 - 50 k
            re.compile(r"(\d{2,3})\s*k?\s*(?:-|to|–|—)\s*(\d{2,3})\s*k", re.IGNORECASE),
        ]

        self.single_patterns = [
            # 40,000 THB or 45000 บาท
            re.compile(r"(?:salary|เงินเดือน|offer|budget)?\s*(?:thb|baht|บาท)?\s*(\d{1,3}(?:,\d{3})+|\d{4,6})\s*(?:thb|baht|บาท|/month|ต่อเดือน)?", re.IGNORECASE),
            re.compile(r"(\d{2,3})\s*k\s*(?:thb|baht|บาท|/month|ต่อเดือน)?", re.IGNORECASE),
        ]

        self.unspecified_keywords = [
            "negotiable",
            "ตามตกลง",
            "ตามโครงสร้าง",
            "ตามประสบการณ์",
            "ขึ้นอยู่กับความสามารถ",
            "disclose",
            "competitive",
            "not specified",
            "undisclosed",
        ]

    def _clean_number(self, val_str: str) -> int:
        clean = val_str.replace(",", "").strip().lower()
        if clean.endswith("k"):
            return int(float(clean[:-1]) * 1000)
        num = int(clean)
        if num < 200:  # e.g., "45" representing 45k
            return num * 1000
        return num

    def parse_salary_text(self, text: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """Extracts min and max salary values from arbitrary text."""
        if not text:
            return None, None, None

        # Check for range patterns
        for pattern in self.range_patterns:
            match = pattern.search(text)
            if match:
                raw = match.group(0)
                try:
                    v1 = self._clean_number(match.group(1))
                    v2 = self._clean_number(match.group(2))
                    min_val, max_val = min(v1, v2), max(v1, v2)
                    # Filter out non-salary numbers (e.g. years 2024-2026 or employee counts)
                    if 15000 <= min_val <= 500000 and 15000 <= max_val <= 500000:
                        return min_val, max_val, raw
                except (ValueError, TypeError):
                    continue

        # Check for single salary mentions
        for pattern in self.single_patterns:
            match = pattern.search(text)
            if match:
                raw = match.group(0)
                try:
                    val = self._clean_number(match.group(1))
                    if 15000 <= val <= 500000:
                        return val, val, raw
                except (ValueError, TypeError):
                    continue

        return None, None, None

    def estimate_role_benchmark(self, job_title: str) -> str:
        """Estimates market standard for Thai tech market when no salary is given."""
        title_lower = job_title.lower() if job_title else ""
        if any(w in title_lower for w in ["intern", "trainee"]):
            return "Internship: 10,000 - 20,000 THB"
        if any(w in title_lower for w in ["senior", "lead", "principal", "manager"]):
            return "Senior/Lead Benchmark: 65,000 - 120,000+ THB"
        if any(w in title_lower for w in ["ai", "machine learning", "ml", "genai", "computer vision"]):
            return "AI/ML Engineer (1-3 yrs): 40,000 - 65,000 THB (High Demand)"
        if any(w in title_lower for w in ["software", "backend", "fullstack", "developer"]):
            return "Software/Backend Engineer (1-3 yrs): 35,000 - 55,000 THB"
        if any(w in title_lower for w in ["data scientist", "data analyst"]):
            return "Data Professional (1-3 yrs): 35,000 - 55,000 THB"
        return "Bangkok Tech Market (1-3 yrs): 35,000 - 55,000 THB"

    def evaluate(
        self,
        salary_text_or_jd: str,
        job_title: str = "",
        expectation: Optional[SalaryExpectation] = None,
    ) -> SalaryEvaluationResult:
        """Evaluates whether a job posting matches the candidate's salary expectations."""
        exp = expectation or self.expectation
        min_salary, max_salary, raw_text = self.parse_salary_text(salary_text_or_jd)

        form_input = f"{exp.min_salary:,} - {exp.max_salary:,} {exp.currency} (Negotiable)"
        thai_input = f"{exp.min_salary:,} - {exp.max_salary:,} บาท (ตามโครงสร้างและสวัสดิการ)"

        if min_salary is not None and max_salary is not None:
            # Explicit salary tag found
            if max_salary < exp.min_salary:
                status = "BELOW"
                is_acceptable = False
                explanation = (
                    f"Listed salary ({min_salary:,} - {max_salary:,} THB) is lower than your "
                    f"minimum threshold of {exp.min_salary:,} THB."
                )
            elif min_salary > exp.max_salary:
                status = "ABOVE"
                is_acceptable = True
                explanation = (
                    f"Listed salary ({min_salary:,} - {max_salary:,} THB) exceeds your target range "
                    f"({exp.min_salary:,} - {exp.max_salary:,} THB). Excellent compensation tier!"
                )
            else:
                status = "MATCH"
                is_acceptable = True
                explanation = (
                    f"Listed salary ({min_salary:,} - {max_salary:,} THB) overlaps directly with your target "
                    f"of {exp.min_salary:,} - {exp.max_salary:,} THB."
                )

            return SalaryEvaluationResult(
                has_salary_tag=True,
                raw_salary_text=raw_text,
                parsed_min=min_salary,
                parsed_max=max_salary,
                match_status=status,
                is_acceptable=is_acceptable,
                explanation=explanation,
                suggested_form_input=form_input,
                thai_suggested_input=thai_input,
            )

        # No explicit salary tag found (Common case on Thai job boards)
        benchmark = self.estimate_role_benchmark(job_title)
        explanation = (
            f"No explicit price tag listed (standard for >70% of Thai tech postings). "
            f"Estimated market standard for '{job_title or 'Tech Role'}': {benchmark}. "
            f"Your expected salary {exp.min_salary:,} - {exp.max_salary:,} THB will be auto-prefilled."
        )

        return SalaryEvaluationResult(
            has_salary_tag=False,
            raw_salary_text=None,
            parsed_min=None,
            parsed_max=None,
            match_status="UNSPECIFIED",
            is_acceptable=exp.include_unspecified,
            explanation=explanation,
            suggested_form_input=form_input,
            thai_suggested_input=thai_input,
        )
