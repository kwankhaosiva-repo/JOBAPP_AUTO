"""Unit tests for the Salary Matcher service.
"""

import pytest
from src.models import SalaryExpectation
from src.services.salary_matcher import SalaryMatcher


def test_parse_explicit_salary_range():
    matcher = SalaryMatcher()

    # Pattern 1: 40,000 - 50,000 บาท
    min_val, max_val, raw = matcher.parse_salary_text("เงินเดือน 40,000 - 50,000 บาท")
    assert min_val == 40000
    assert max_val == 50000
    assert "40,000 - 50,000" in raw

    # Pattern 2: 45k - 60k THB
    min_val, max_val, raw = matcher.parse_salary_text("Offer: 45k - 60k THB/month")
    assert min_val == 45000
    assert max_val == 60000

    # Pattern 3: Single salary 45,000 THB
    min_val, max_val, raw = matcher.parse_salary_text("Budget: 45,000 THB")
    assert min_val == 45000
    assert max_val == 45000


def test_evaluate_within_bracket():
    matcher = SalaryMatcher()
    exp = SalaryExpectation(min_salary=40000, max_salary=45000)

    res = matcher.evaluate("40,000 - 45,000 THB", job_title="AI Engineer", expectation=exp)
    assert res.has_salary_tag is True
    assert res.match_status == "MATCH"
    assert res.is_acceptable is True


def test_evaluate_below_bracket():
    matcher = SalaryMatcher()
    exp = SalaryExpectation(min_salary=40000, max_salary=45000)

    res = matcher.evaluate("25,000 - 32,000 บาท", job_title="Junior AI Engineer", expectation=exp)
    assert res.has_salary_tag is True
    assert res.match_status == "BELOW"
    assert res.is_acceptable is False


def test_evaluate_unpriced_role():
    matcher = SalaryMatcher()
    exp = SalaryExpectation(min_salary=40000, max_salary=45000, include_unspecified=True)

    # Job description with no salary tag (most common on Thai boards)
    jd = "Seeking an AI Engineer with Python, FastAPI, and Cloud Run experience. Competitive benefits."
    res = matcher.evaluate(jd, job_title="AI Engineer", expectation=exp)

    assert res.has_salary_tag is False
    assert res.match_status == "UNSPECIFIED"
    assert res.is_acceptable is True
    assert "40,000 - 45,000" in res.suggested_form_input
