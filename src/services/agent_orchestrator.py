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
    AutoDiscoverRequest,
    AutoDiscoverResponse,
    CompanyPrepReport,
    CompanyPrepRequest,
    CompatibilityRequest,
    CompatibilityResult,
    CoverLetterRequest,
    DiscoveredJobItem,
)
from src.services.company_prep_service import CompanyPrepService
from src.services.compatibility_service import CompatibilityService
from src.services.cover_letter_service import CoverLetterService
from src.services.history_tracker import HistoryTracker
from src.services.job_discovery_service import JobDiscoveryService
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
        job_discovery_service: Optional[JobDiscoveryService] = None,
    ):
        self.evaluator_agent = compatibility_service or CompatibilityService()
        self.tailoring_agent = cover_letter_service or CoverLetterService()
        self.prep_agent = company_prep_service or CompanyPrepService()
        self.tracker = history_tracker or HistoryTracker()
        self.platform_manager = platform_manager or PlatformManager()
        self.scout_agent = scraper_service or ScraperService()
        self.discovery_agent = job_discovery_service or JobDiscoveryService(self.platform_manager)

    def auto_discover_and_shortlist(
        self, req: AutoDiscoverRequest
    ) -> AutoDiscoverResponse:
        """Automated Multi-Platform Discovery -> Compatibility Evaluation -> Considering Shortlist.

        Finds jobs across platforms without requiring the user to paste links,
        scores every job against Resume + aboutme.txt + Salary, and automatically
        tags compatible jobs as 'Considering' in CSV & Excel.
        """
        raw_jobs = self.discovery_agent.discover_jobs(
            keywords=req.keywords,
            platforms=req.platforms,
            location=req.location,
            max_results=req.max_results,
        )

        existing_records = self.tracker.load_records()
        existing_map: Dict[tuple, int] = {
            (r.company.strip().lower(), r.job_position.strip().lower()): (r.id or 0)
            for r in existing_records
        }

        discovered_items: List[DiscoveredJobItem] = []
        compatible_count = 0
        newly_saved_count = 0
        already_in_history_count = 0
        engine_used = "smart_profile_matcher"

        for raw in raw_jobs:
            comp_name = raw["company_name"]
            job_pos = raw["job_position"]
            plat_id = raw["platform"]
            jd_text = raw["job_description"]
            link = raw["link"]

            comp_req = CompatibilityRequest(
                company_name=comp_name,
                job_position=job_pos,
                job_description=jd_text,
                platform=plat_id,
                link=link,
                min_salary=req.min_salary,
                max_salary=req.max_salary,
                llm_provider=req.llm_provider,
            )
            evaluation = self.evaluator_agent.evaluate(comp_req)
            engine_used = evaluation.engine_used

            cl_req = CoverLetterRequest(
                company_name=comp_name,
                job_position=job_pos,
                job_description=jd_text,
                target_salary_min=req.min_salary,
                target_salary_max=req.max_salary,
                focus_domain=evaluation.suggested_domain,
            )
            cover_letter = self.tailoring_agent.generate(cl_req)

            meets_threshold = (
                evaluation.overall_score >= req.min_score_threshold
                and evaluation.salary_fit_score >= 50
            )
            if meets_threshold:
                compatible_count += 1

            lookup_key = (comp_name.strip().lower(), job_pos.strip().lower())
            already_exists = lookup_key in existing_map
            saved_id: Optional[int] = existing_map.get(lookup_key)
            saved_now = False

            if already_exists:
                already_in_history_count += 1
            elif req.auto_save_considering and meets_threshold:
                note_summary = (
                    f"Auto-Discovered ({plat_id}) | Match: {evaluation.overall_score}% "
                    f"(Skills: {evaluation.skill_match_score}%, Goals: {evaluation.goal_alignment_score}%)"
                )
                new_rec = ApplicationRecord(
                    company=comp_name,
                    link=link,
                    jd=jd_text,
                    industry=raw.get("industry", ""),
                    job_position=job_pos,
                    location=raw.get("location", "Bangkok, Thailand"),
                    offer_salary=raw.get("salary_tag", ""),
                    priority="First" if evaluation.overall_score >= 82 else "Second",
                    status="Considering",
                    salary=f"{req.min_salary:,} - {req.max_salary:,} THB",
                    job_letter=cover_letter,
                    notes=note_summary,
                )
                added = self.tracker.add_record(new_rec)
                saved_id = added.id
                existing_map[lookup_key] = saved_id or 0
                saved_now = True
                newly_saved_count += 1

            discovered_items.append(
                DiscoveredJobItem(
                    company_name=comp_name,
                    job_position=job_pos,
                    platform=plat_id,
                    platform_name=raw.get("platform_name", plat_id.title()),
                    location=raw.get("location", "Bangkok, Thailand"),
                    industry=raw.get("industry", ""),
                    salary_tag=raw.get("salary_tag", "Not specified"),
                    link=link,
                    job_description=jd_text,
                    source_type=raw.get("source_type", "platform_feed"),
                    evaluation=evaluation,
                    cover_letter=cover_letter,
                    saved_to_considering=saved_now,
                    already_in_history=already_exists,
                    record_id=saved_id,
                )
            )

        # Sort highest compatibility score first
        discovered_items.sort(key=lambda item: item.evaluation.overall_score, reverse=True)

        return AutoDiscoverResponse(
            total_found=len(discovered_items),
            compatible_count=compatible_count,
            newly_saved_count=newly_saved_count,
            already_in_history_count=already_in_history_count,
            engine_used=engine_used,
            requires_api_key=False,
            jobs=discovered_items,
        )

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
