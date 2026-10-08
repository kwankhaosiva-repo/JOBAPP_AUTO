"""Unit tests for AI Job Compatibility Evaluation, Multi-Agent Orchestrator,
Excel export sync, and Company Presentation Preparation.
"""

import shutil
from src.config import CSV_HISTORY_PATH
from src.models import AutoDiscoverRequest, CompanyPrepRequest, CompatibilityRequest
from src.services.agent_orchestrator import AgentOrchestrator
from src.services.company_prep_service import CompanyPrepService
from src.services.compatibility_service import CompatibilityService
from src.services.history_tracker import HistoryTracker
from src.services.job_discovery_service import JobDiscoveryService


def test_compatibility_high_match():
    service = CompatibilityService()
    req = CompatibilityRequest(
        company_name="SCBX",
        job_position="AI Engineer (FinTech)",
        job_description=(
            "We are looking for an AI Engineer with experience in Python, FastAPI, Docker, "
            "GCP Cloud Run, PyTorch, RAG, LangChain, and SQL to build financial AI solutions."
        ),
        min_salary=40000,
        max_salary=45000,
        llm_provider="heuristic",
    )
    res = service.evaluate(req)
    assert res.overall_score >= 80
    assert res.is_compatible is True
    assert res.recommended_status == "Considering"
    assert "Python" in res.matched_skills
    assert "FastAPI" in res.matched_skills
    assert res.suggested_domain == "fintech"


def test_compatibility_low_salary_penalty():
    service = CompatibilityService()
    req = CompatibilityRequest(
        company_name="SmallShop",
        job_position="Junior Support",
        job_description="Salary: 18,000 - 22,000 THB. Basic office work.",
        min_salary=40000,
        max_salary=45000,
        llm_provider="heuristic",
    )
    res = service.evaluate(req)
    assert res.is_compatible is False
    assert res.salary_fit_score < 50


def test_orchestrator_shortlist_considering_to_submitted_and_excel(tmp_path):
    test_csv = tmp_path / "test_apps.csv"
    test_xlsx = tmp_path / "test_apps.xlsx"
    shutil.copyfile(CSV_HISTORY_PATH, test_csv)

    tracker = HistoryTracker(csv_path=test_csv, excel_path=test_xlsx)
    orchestrator = AgentOrchestrator(history_tracker=tracker)

    # 1. Run pipeline to auto-shortlist compatible role as 'Considering'
    result = orchestrator.evaluate_and_shortlist(
        company_name="Kasikorn Business-Technology Group (KBTG)",
        job_position="AI Product Engineer",
        job_description="Python, FastAPI, LLM, RAG, Docker, Cloud Run, FinTech banking innovation.",
        platform="linkedin",
        auto_save_if_compatible=True,
        llm_provider="heuristic",
    )

    assert result["saved_to_history"] is True
    rec = result["record"]
    assert rec["status"] == "Considering"
    assert rec["resume_sent"] == ""  # Not sent yet while Considering
    assert test_xlsx.exists()

    # 2. User manually submits and updates status from 'Considering' -> 'Submitted'
    record_id = rec["id"]
    updated = tracker.update_record_status(record_id, "Submitted")
    assert updated is True

    reloaded = tracker.load_records()[record_id - 1]
    assert reloaded.status == "Submitted"
    assert reloaded.resume_sent != ""  # Submission date automatically stamped


def test_auto_discover_and_shortlist_across_platforms(tmp_path):
    test_csv = tmp_path / "test_discover.csv"
    test_xlsx = tmp_path / "test_discover.xlsx"
    shutil.copyfile(CSV_HISTORY_PATH, test_csv)

    tracker = HistoryTracker(csv_path=test_csv, excel_path=test_xlsx)
    discovery = JobDiscoveryService()
    orchestrator = AgentOrchestrator(
        history_tracker=tracker,
        job_discovery_service=discovery,
    )

    req = AutoDiscoverRequest(
        keywords="AI Engineer, Machine Learning, Python",
        platforms=["linkedin", "jobsdb", "jobthai", "jobbkk", "jobtopgun", "workventure"],
        min_salary=40000,
        max_salary=45000,
        min_score_threshold=65,
        auto_save_considering=True,
        max_results=6,
        llm_provider="heuristic",
    )
    resp = orchestrator.auto_discover_and_shortlist(req)

    assert resp.total_found == 6
    assert resp.compatible_count >= 4
    assert resp.newly_saved_count >= 1
    assert resp.requires_api_key is False
    # Verify sorted descending by compatibility score
    scores = [j.evaluation.overall_score for j in resp.jobs]
    assert scores == sorted(scores, reverse=True)

    # Re-running should deduplicate and not add duplicate rows
    resp_second = orchestrator.auto_discover_and_shortlist(req)
    assert resp_second.newly_saved_count == 0
    assert resp_second.already_in_history_count >= 1


def test_company_presentation_prep_service():
    prep_service = CompanyPrepService()
    req = CompanyPrepRequest(
        company_name="SCB TechX",
        job_position="AI Engineer",
        industry="FinTech",
        job_description="Building GenAI, RAG, and scalable backend services on cloud.",
    )
    report = prep_service.generate_prep_report(req)

    assert report.company_name == "SCB TechX"
    assert len(report.presentation_slides) == 5
    assert len(report.interview_qas) >= 3
    assert len(report.research_links) >= 3
    assert "Slide 1:" in report.markdown_deck
    assert "Slide 5:" in report.markdown_deck

