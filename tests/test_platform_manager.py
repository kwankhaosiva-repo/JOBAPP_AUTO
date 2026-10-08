"""Unit tests for the Platform Manager and Platform Adapters.
"""

from src.models import CandidateProfile, SalaryExpectation
from src.services.platforms.platform_manager import PlatformManager


def test_platform_registry():
    pm = PlatformManager()
    platforms = pm.list_platforms()
    platform_ids = {p["id"] for p in platforms}

    # Verify all 6 requested platforms exist
    required = {"linkedin", "jobsdb", "jobthai", "jobbkk", "jobtopgun", "workventure"}
    assert required.issubset(platform_ids)


def test_search_url_generation():
    pm = PlatformManager()

    linkedin = pm.get_platform("linkedin")
    assert "keywords=AI%20Engineer" in linkedin.build_search_url("AI Engineer", "Bangkok")

    jobthai = pm.get_platform("jobthai")
    assert "keyword=AI%20Engineer" in jobthai.build_search_url("AI Engineer")

    jobsdb = pm.get_platform("jobsdb")
    assert "search-jobs/ai-engineer-in-bangkok" in jobsdb.build_search_url("AI Engineer", "Bangkok")


def test_autofill_payload():
    pm = PlatformManager()
    workventure = pm.get_platform("workventure")

    candidate = CandidateProfile(name="Kwankhao Sivasomboon", email="Kwankhaosiva@gmail.com")
    exp = SalaryExpectation(min_salary=40000, max_salary=45000)

    payload = workventure.prepare_autofill_payload(candidate=candidate, salary_exp=exp)
    assert payload["candidate_name_en"] == "Kwankhao Sivasomboon"
    assert payload["expected_salary_min"] == 40000
    assert payload["expected_salary_max"] == 45000
    assert "40,000 - 45,000 THB" in payload["expected_salary_text_en"]
