"""History tracking service (CSV & Excel Bi-Directional Sync).

Handles reading, updating, and writing application records to:
- docs/Job Application - Second Jobber.csv
- docs/Job Application - Second Jobber.xlsx
Supports the semi-auto workflow: 'Considering' -> 'Submitted' / 'Resume Sent' -> 'Interview Scheduled'.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from src.config import CSV_HEADERS, CSV_HISTORY_PATH, EXCEL_HISTORY_PATH
from src.models import ApplicationRecord


class HistoryTracker:
    """Manages the job application history in both CSV and Excel (.xlsx) formats."""

    def __init__(
        self,
        csv_path: Path = CSV_HISTORY_PATH,
        excel_path: Path = EXCEL_HISTORY_PATH,
    ):
        self.csv_path = csv_path
        self.excel_path = excel_path

    def _ensure_csv_exists(self) -> None:
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([""] * len(CSV_HEADERS))
                writer.writerow(CSV_HEADERS)

    def load_records(self) -> List[ApplicationRecord]:
        """Loads all application records from the CSV."""
        self._ensure_csv_exists()
        records: List[ApplicationRecord] = []

        with open(self.csv_path, mode="r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return records

        # Line 0 is the empty spacer row; Line 1 is headers
        reader = csv.reader(lines[1:])
        try:
            _ = next(reader)  # Header row
        except StopIteration:
            return records

        for idx, row in enumerate(reader):
            if not row or not any(field.strip() for field in row):
                continue

            padded = row + [""] * (len(CSV_HEADERS) - len(row))

            record = ApplicationRecord(
                id=idx + 1,
                company=padded[0].strip(),
                link=padded[1].strip(),
                jd=padded[2].strip(),
                employees=padded[3].strip(),
                industry=padded[4].strip(),
                job_position=padded[5].strip(),
                location=padded[6].strip(),
                offer_salary=padded[7].strip(),
                priority=padded[8].strip(),
                status=padded[9].strip() or "Resume Sent",
                salary=padded[10].strip(),
                hr_email=padded[11].strip(),
                resume_sent=padded[12].strip(),
                hr_contacted=padded[13].strip(),
                interview_date=padded[14].strip(),
                test_date=padded[15].strip(),
                job_letter=padded[16].strip(),
                notes=padded[17].strip(),
            )
            records.append(record)

        return records

    def add_record(self, record: ApplicationRecord) -> ApplicationRecord:
        """Appends a new application record to CSV and syncs Excel."""
        self._ensure_csv_exists()

        # Only set resume_sent date automatically if status is Submitted or Resume Sent
        if not record.resume_sent and record.status in ("Submitted", "Resume Sent"):
            now = datetime.now()
            record.resume_sent = f"{now.month}/{now.day}/{now.year}"

        records = self.load_records()
        record.id = len(records) + 1
        records.append(record)

        self._rewrite_all(records)
        self.export_to_excel(records)
        return record

    def update_record_status(
        self, record_id: int, new_status: str, notes: Optional[str] = None
    ) -> bool:
        """Updates the status and optional notes of a specific application record."""
        records = self.load_records()
        if not (1 <= record_id <= len(records)):
            return False

        target = records[record_id - 1]
        target.status = new_status

        # Stamp submission date when transitioning from Considering -> Submitted / Resume Sent
        if new_status in ("Submitted", "Resume Sent") and not target.resume_sent:
            now = datetime.now()
            target.resume_sent = f"{now.month}/{now.day}/{now.year}"

        if notes:
            target.notes = (target.notes + "\n" + notes).strip()

        self._rewrite_all(records)
        self.export_to_excel(records)
        return True

    def _rewrite_all(self, records: List[ApplicationRecord]) -> None:
        """Rewrites the full CSV while preserving header formatting."""
        with open(self.csv_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([""] * len(CSV_HEADERS))
            writer.writerow(CSV_HEADERS)
            for r in records:
                writer.writerow([
                    r.company,
                    r.link,
                    r.jd,
                    r.employees,
                    r.industry,
                    r.job_position,
                    r.location,
                    r.offer_salary,
                    r.priority,
                    r.status,
                    r.salary,
                    r.hr_email,
                    r.resume_sent,
                    r.hr_contacted,
                    r.interview_date,
                    r.test_date,
                    r.job_letter,
                    r.notes,
                ])

    def export_to_excel(self, records: Optional[List[ApplicationRecord]] = None) -> Path:
        """Exports all records into a formatted Excel (.xlsx) workbook."""
        if records is None:
            records = self.load_records()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Job Applications"

        # Header styling
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        ws.append(CSV_HEADERS)
        for col_idx in range(1, len(CSV_HEADERS) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="left", vertical="center")

        # Status fills
        considering_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        submitted_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        interview_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")

        for r in records:
            row_vals = [
                r.company,
                r.link,
                r.jd,
                r.employees,
                r.industry,
                r.job_position,
                r.location,
                r.offer_salary,
                r.priority,
                r.status,
                r.salary,
                r.hr_email,
                r.resume_sent,
                r.hr_contacted,
                r.interview_date,
                r.test_date,
                r.job_letter,
                r.notes,
            ]
            ws.append(row_vals)
            curr_row = ws.max_row
            status_cell = ws.cell(row=curr_row, column=10)
            if r.status == "Considering":
                status_cell.fill = considering_fill
            elif r.status in ("Submitted", "Resume Sent"):
                status_cell.fill = submitted_fill
            elif "Interview" in r.status or r.status == "HR Contacted":
                status_cell.fill = interview_fill

        # Set readable column widths
        col_widths = {
            1: 26,  # Company
            2: 32,  # Link
            3: 40,  # JD
            4: 14,  # Employees
            5: 18,  # Industry
            6: 28,  # Job Position
            7: 20,  # Location
            8: 16,  # Offer Salary
            9: 12,  # Priority
            10: 18, # Status
            11: 20, # Salary
            12: 22, # HR Email
            13: 15, # Resume Sent
            14: 15, # HR Contacted
            15: 15, # Interview date
            16: 15, # Test date
            17: 45, # Job Letter
            18: 30, # Notes
        }
        for col_idx, width in col_widths.items():
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        self.excel_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(self.excel_path))
        return self.excel_path

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculates tracking dashboard metrics including Considering & Submitted queues."""
        records = self.load_records()
        total = len(records)
        status_counts: Dict[str, int] = {}
        for r in records:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1

        considering_count = status_counts.get("Considering", 0)
        submitted_count = sum(
            1
            for r in records
            if r.status in ("Submitted", "Resume Sent")
            or (r.resume_sent and r.status != "Considering")
        )
        not_pass = status_counts.get("Not Pass?", 0)
        interviews = (
            status_counts.get("Interview Scheduled", 0)
            + status_counts.get("Interview", 0)
            + status_counts.get("HR Contacted", 0)
            + status_counts.get("Technical Test", 0)
        )

        return {
            "total_applications": total,
            "considering_count": considering_count,
            "resumes_sent": submitted_count,
            "not_pass": not_pass,
            "interviewing": interviews,
            "status_breakdown": status_counts,
        }
