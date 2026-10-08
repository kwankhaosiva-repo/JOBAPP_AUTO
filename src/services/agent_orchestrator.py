"""Multi-Agent Pipeline Orchestrator for Semi-Automated Job Applications.

Coordinates 4 specialized agents without over-engineered conversational loops:
1. ScoutAgent (ScraperService + PlatformManager): Extracts JD & platform metadata
2. EvaluatorAgent (CompatibilityService): Scores resume, career goals, and salary fit
3. TailoringAgent (CoverLetterService): Synthesizes domain-matched cover letter
4. PrepAgent (CompanyPrepService): Builds company research & 5-slide presentation kit
"""

from typing import Any, Dict, List, Optional

from src.models import (
    ApplicationRecord,
    CompanyPrepReport,
    CompanyPrepRequest,
    CompatibilityRequest,
    CompatibilityResult,
    CoverLetterRequest,
)
from src.services.company_prep_service import CompanyPrepService
from src.services.compatibility_service import CompatibilityService
from src.services.cover_letter_service import CoverLetterService
from src.services.history_tracker import HistoryTracker
from src.services.platforms.platform_manager import PlatformManager
from src.services.scraper_service import ScraperService


class AgentOrchestrator:
    """Coordinates specialist agents across the semi-auto job application lifecycle."""

    def __init__(
        self,
        compatibility_service: Optional[CompatibilityService] = None,
        cover_letter_service: Optional[CoverLetterService] = None,
        company_prep_service: Optional[CompanyPrepService] = None,
        history_tracker: Optional[HistoryTracker] = None,
        platform_manager: Optional[PlatformManager] = None,
        scraper_service: Optional[ScraperService] = None,
    ):
        self.evaluator_agent = compatibility_service or CompatibilityService()
        self.tailoring_agent = cover_letter_service or CoverLetterService()
        self.prep_agent = company_prep_service or CompanyPrepService()
        self.tracker = history_tracker or HistoryTracker()
        self.platform_manager = platform_manager or PlatformManager()
        self.scout_agent = scraper_service or ScraperService()

    def evaluate_and_shortlist(
        self,
        company_name: str,
        job_position: str,
        job_description: str = "",
        link: str = "",
        platform: str = "linkedin",
        industry: str = "",
        location: str = "Bangkok, Thailand",
        priority: str = "First",
        min_salary: int = 40000,
        max_salary: int = 45000,
        auto_save_if_compatible: bool = True,
        force_save: bool = False,
        llm_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the Scout -> Evaluator -> Tailoring pipeline.

        If the role meets compatibility thresholds (or force_save=True), automatically
        tags the job status as 'Considering', generates a tailored cover letter,
        and logs it to CSV & Excel for the user's manual submission review.
        """
        # Step 1: Scout Agent — enrich JD from URL if JD is empty and URL is provided
        effective_jd = job_description.strip()
        if not effective_jd and link:
            fetched = self.scout_agent.fetch_page_text(link)
            if fetched:
                effective_jd = fetched[:4000]

        # Auto-detect platform from link if available
        if link:
            detected_plat = self.platform_manager.detect_platform_from_url(link)
            if detected_plat:
                platform = detected_plat.platform_id

        # Step 2: Evaluator Agent — score compatibility against Resume + Goals + Salary
        comp_req = CompatibilityRequest(
            company_name=company_name,
            job_position=job_position,
            job_description=effective_jd,
            platform=platform,
            link=link,
            min_salary=min_salary,
            max_salary=max_salary,
            llm_provider=llm_provider,
        )
        evaluation: CompatibilityResult = self.evaluator_agent.evaluate(comp_req)

        # Step 3: Tailoring Agent — generate customized cover letter using detected domain
        cl_req = CoverLetterRequest(
            company_name=company_name,
            job_position=job_position,
            job_description=effective_jd,
            target_salary_min=min_salary,
            target_salary_max=max_salary,
            focus_domain=evaluation.suggested_domain,
        )
        cover_letter = self.tailoring_agent.generate(cl_req)

        # Step 4: Tracker Sync — save as 'Considering' if compatible
        saved_record: Optional[ApplicationRecord] = None
        should_save = force_save or (auto_save_if_compatible and evaluation.is_compatible)

        if should_save:
            note_summary = (
                f"Platform: {platform} | AI Match: {evaluation.overall_score}% "
                f"(Skills: {evaluation.skill_match_score}%, Goals: {evaluation.goal_alignment_score}%)"
            )
            new_rec = ApplicationRecord(
                company=company_name,
                link=link,
                jd=effective_jd,
                industry=industry,
                job_position=job_position,
                location=location,
                priority=priority,
                status="Considering",
                salary=f"{min_salary:,} - {max_salary:,} THB",
                job_letter=cover_letter,
                notes=note_summary,
            )
            saved_record = self.tracker.add_record(new_rec)

        return {
            "evaluation": evaluation.model_dump(),
            "cover_letter": cover_letter,
            "saved_to_history": saved_record is not None,
            "record": saved_record.model_dump() if saved_record else None,
        }

    def prepare_presentation_for_submitted(
        self,
        record_id: Optional[int] = None,
        company_name: str = "",
        job_position: str = "",
        industry: str = "",
        job_description: str = "",
    ) -> CompanyPrepReport:
        """Runs the PrepAgent to build a 5-slide presentation & company research brief."""
        if record_id is not None:
            records = self.tracker.load_records()
            if 1 <= record_id <= len(records):
                rec = records[record_id - 1]
                company_name = company_name or rec.company
                job_position = job_position or rec.job_position
                industry = industry or rec.industry
                job_description = job_description or rec.jd

        req = CompanyPrepRequest(
            record_id=record_id,
            company_name=company_name,
            job_position=job_position,
            industry=industry,
            job_description=job_description,
        )
        return self.prep_agent.generate_prep_report(req)
