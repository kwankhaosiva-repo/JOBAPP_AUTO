"""CLI Orchestration entrypoint for JOB_APP_AUTO.

Allows searching platforms, evaluating AI compatibility, shortlisting jobs
as 'Considering', exporting CSV/Excel, generating tailored cover letters,
and building 5-slide company presentation kits from the terminal.
"""

import argparse
import sys
import uvicorn

from src.config import DEFAULT_MAX_SALARY, DEFAULT_MIN_SALARY
from src.models import ApplicationRecord, CoverLetterRequest, SalaryExpectation
from src.services.agent_orchestrator import AgentOrchestrator
from src.services.cover_letter_service import CoverLetterService
from src.services.history_tracker import HistoryTracker
from src.services.platforms.platform_manager import PlatformManager
from src.services.salary_matcher import SalaryMatcher


def cmd_stats(args):
    tracker = HistoryTracker()
    stats = tracker.get_summary_stats()
    print("\n=======================================================")
    print("       JOB_APP_AUTO - APPLICATION DASHBOARD STATS       ")
    print("=======================================================")
    print(f" Total Applications Tracked: {stats['total_applications']}")
    print(f" Considering (Shortlisted):  {stats['considering_count']}")
    print(f" Submitted / Resumes Sent:   {stats['resumes_sent']}")
    print(f" Interviewing / In Progress: {stats['interviewing']}")
    print(f" Status 'Not Pass?':         {stats['not_pass']}")
    print("-------------------------------------------------------")
    print(" Status Breakdown:")
    for status, count in stats["status_breakdown"].items():
        print(f"   • {status or 'Unspecified'}: {count}")
    print("=======================================================\n")


def cmd_search(args):
    pm = PlatformManager()
    plat = pm.get_platform(args.platform)
    if not plat:
        print(f"Error: Unknown platform '{args.platform}'.")
        sys.exit(1)

    url = plat.build_search_url(keywords=args.keywords, location=args.location)
    print(f"\n[Platform: {plat.name}]")
    print(f"Search Query: '{args.keywords}' in '{args.location}'")
    print(f"URL: {url}")

    if args.open:
        print("Opening in default browser...")
        pm.launch_browser_url(url)


def cmd_evaluate_salary(args):
    matcher = SalaryMatcher()
    exp = SalaryExpectation(min_salary=args.min_salary, max_salary=args.max_salary)
    res = matcher.evaluate(args.text, job_title=args.role, expectation=exp)

    print("\n=======================================================")
    print("                SALARY EVALUATION REPORT               ")
    print("=======================================================")
    print(f" Target Range:        {exp.min_salary:,} - {exp.max_salary:,} THB")
    print(f" Detected Salary Tag: {res.raw_salary_text or 'None (Unspecified)'}")
    print(f" Match Verdict:       {res.match_status} (Acceptable: {res.is_acceptable})")
    print(f" Analysis:            {res.explanation}")
    print("-------------------------------------------------------")
    print(f" Suggested Form (EN): {res.suggested_form_input}")
    print(f" Suggested Form (TH): {res.thai_suggested_input}")
    print("=======================================================\n")


def cmd_evaluate_compat(args):
    orchestrator = AgentOrchestrator()
    res = orchestrator.evaluate_and_shortlist(
        company_name=args.company,
        job_position=args.role,
        job_description=args.jd or "",
        link=args.link or "",
        platform=args.platform,
        min_salary=args.min_salary,
        max_salary=args.max_salary,
        auto_save_if_compatible=args.shortlist,
        llm_provider=args.provider,
    )
    ev = res["evaluation"]
    print("\n=======================================================")
    print("         AI JOB COMPATIBILITY EVALUATION REPORT        ")
    print("=======================================================")
    print(f" Company & Role:      {args.company} — {args.role}")
    print(f" Engine Used:         {ev['engine_used']}")
    print(f" Overall Match Score: {ev['overall_score']}% ({ev['verdict_label']})")
    print(f"   • Resume Skills:   {ev['skill_match_score']}%")
    print(f"   • Goal Alignment:  {ev['goal_alignment_score']}%")
    print(f"   • Salary Fit:      {ev['salary_fit_score']}%")
    print(f" Matched Skills:      {', '.join(ev['matched_skills']) or 'General'}")
    print(f" Career Goals Fit:    {', '.join(ev['matched_goals']) or 'Engineering'}")
    print(f" Analysis:            {ev['reasoning']}")
    if res["saved_to_history"]:
        rec = res["record"]
        print("-------------------------------------------------------")
        print(f" [SHORTLISTED] Saved as #{rec['id']} with status '{rec['status']}' in CSV & Excel!")
    print("=======================================================\n")


def cmd_prep(args):
    orchestrator = AgentOrchestrator()
    report = orchestrator.prepare_presentation_for_submitted(
        record_id=args.id,
        company_name=args.company or "",
        job_position=args.role or "",
        job_description=args.jd or "",
    )
    print("\n" + report.markdown_deck + "\n")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report.markdown_deck)
        print(f"Saved presentation prep deck to: {args.output}")


def cmd_export_excel(args):
    tracker = HistoryTracker()
    path = tracker.export_to_excel()
    print(f"\nExported formatted Excel workbook to: {path}\n")


def cmd_cover_letter(args):
    service = CoverLetterService()
    req = CoverLetterRequest(
        company_name=args.company,
        job_position=args.role,
        job_description=args.jd or "",
        target_salary_min=args.min_salary,
        target_salary_max=args.max_salary,
    )
    letter = service.generate(req)

    print("\n=======================================================")
    print(f" COVER LETTER FOR: {args.company} ({args.role})")
    print("=======================================================\n")
    print(letter)
    print("\n=======================================================\n")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(letter)
        print(f"Saved cover letter to: {args.output}")


def cmd_log_app(args):
    tracker = HistoryTracker()
    record = ApplicationRecord(
        company=args.company,
        link=args.link or "",
        jd=args.jd or "",
        job_position=args.role,
        salary=f"{args.min_salary:,} - {args.max_salary:,} THB",
        status=args.status,
        notes=args.notes or "",
    )
    added = tracker.add_record(record)
    print(f"\nSuccessfully logged application #{added.id} for '{args.company}' (Status: {added.status}) into CSV & Excel!")


def cmd_serve(args):
    print(f"\nStarting JOB_APP_AUTO Web Dashboard on http://{args.host}:{args.port} ...")
    uvicorn.run("app:app", host=args.host, port=args.port, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(
        description="JOB_APP_AUTO: Semi-Auto Multi-Agent Job Application & Presentation Prep Suite"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # stats
    sub_stats = subparsers.add_parser("stats", help="Show application metrics from CSV")
    sub_stats.set_defaults(func=cmd_stats)

    # search
    sub_search = subparsers.add_parser("search", help="Search Thai & Global job boards")
    sub_search.add_argument(
        "--platform",
        default="linkedin",
        choices=["linkedin", "jobsdb", "jobthai", "jobbkk", "jobtopgun", "workventure"],
        help="Target platform",
    )
    sub_search.add_argument("--keywords", default="AI Engineer", help="Job search keywords")
    sub_search.add_argument("--location", default="Bangkok", help="Location")
    sub_search.add_argument("--open", action="store_true", help="Open in browser")
    sub_search.set_defaults(func=cmd_search)

    # evaluate-salary
    sub_eval = subparsers.add_parser("evaluate-salary", help="Evaluate salary against targets")
    sub_eval.add_argument("--text", required=True, help="Job description text or salary string")
    sub_eval.add_argument("--role", default="", help="Job title for market benchmarking")
    sub_eval.add_argument("--min-salary", type=int, default=DEFAULT_MIN_SALARY)
    sub_eval.add_argument("--max-salary", type=int, default=DEFAULT_MAX_SALARY)
    sub_eval.set_defaults(func=cmd_evaluate_salary)

    # evaluate-compat
    sub_compat = subparsers.add_parser("evaluate-compat", help="Evaluate job compatibility with AI & profile")
    sub_compat.add_argument("--company", required=True, help="Company name")
    sub_compat.add_argument("--role", required=True, help="Job position")
    sub_compat.add_argument("--jd", default="", help="Job description text")
    sub_compat.add_argument("--link", default="", help="Job posting URL")
    sub_compat.add_argument("--platform", default="linkedin", help="Platform ID")
    sub_compat.add_argument("--min-salary", type=int, default=DEFAULT_MIN_SALARY)
    sub_compat.add_argument("--max-salary", type=int, default=DEFAULT_MAX_SALARY)
    sub_compat.add_argument("--provider", default=None, help="LLM provider: auto, ollama, openai, heuristic")
    sub_compat.add_argument("--shortlist", action="store_true", help="Save to CSV & Excel as 'Considering' if compatible")
    sub_compat.set_defaults(func=cmd_evaluate_compat)

    # prep
    sub_prep = subparsers.add_parser("prep", help="Generate company research & 5-slide presentation deck")
    sub_prep.add_argument("--id", type=int, default=None, help="Record ID from CSV")
    sub_prep.add_argument("--company", default="", help="Company name")
    sub_prep.add_argument("--role", default="", help="Job position")
    sub_prep.add_argument("--jd", default="", help="Job description")
    sub_prep.add_argument("--output", default="", help="Save markdown presentation deck to file")
    sub_prep.set_defaults(func=cmd_prep)

    # export-excel
    sub_excel = subparsers.add_parser("export-excel", help="Sync and export CSV history to Excel (.xlsx)")
    sub_excel.set_defaults(func=cmd_export_excel)

    # cover-letter
    sub_cl = subparsers.add_parser("cover-letter", help="Generate tailored cover letter")
    sub_cl.add_argument("--company", required=True, help="Target company name")
    sub_cl.add_argument("--role", required=True, help="Target job position")
    sub_cl.add_argument("--jd", default="", help="Job description snippet")
    sub_cl.add_argument("--min-salary", type=int, default=DEFAULT_MIN_SALARY)
    sub_cl.add_argument("--max-salary", type=int, default=DEFAULT_MAX_SALARY)
    sub_cl.add_argument("--output", default="", help="Optional output text file path")
    sub_cl.set_defaults(func=cmd_cover_letter)

    # log-app
    sub_log = subparsers.add_parser("log-app", help="Log an application into CSV & Excel")
    sub_log.add_argument("--company", required=True, help="Company name")
    sub_log.add_argument("--role", required=True, help="Job position")
    sub_log.add_argument("--link", default="", help="Job posting link")
    sub_log.add_argument("--jd", default="", help="Job description")
    sub_log.add_argument("--status", default="Considering", help="Status (default: Considering)")
    sub_log.add_argument("--min-salary", type=int, default=DEFAULT_MIN_SALARY)
    sub_log.add_argument("--max-salary", type=int, default=DEFAULT_MAX_SALARY)
    sub_log.add_argument("--notes", default="", help="Notes")
    sub_log.set_defaults(func=cmd_log_app)

    # serve
    sub_serve = subparsers.add_parser("serve", help="Launch interactive Web Dashboard")
    sub_serve.add_argument("--host", default="127.0.0.1", help="Host address")
    sub_serve.add_argument("--port", type=int, default=8000, help="Port number")
    sub_serve.add_argument("--reload", action="store_true", help="Enable auto-reload")
    sub_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
