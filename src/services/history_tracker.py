"""History tracking service.

Handles reading, updating, and writing application records to
docs/Job Application - Second Jobber.csv without corrupting multi-line
fields or the original CSV structure.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import CSV_HEADERS, CSV_HISTORY_PATH
from src.models import ApplicationRecord


class HistoryTracker:
    """Manages the job application history CSV file."""

    def __init__(self, csv_path: Path = CSV_HISTORY_PATH):
        self.csv_path = csv_path

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

            # Ensure row has at least 18 elements
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
        """Appends a new application record to the CSV safely."""
        self._ensure_csv_exists()

        if not record.resume_sent:
            now = datetime.now()
            record.resume_sent = f"{now.month}/{now.day}/{now.year}"

        records = self.load_records()
        record.id = len(records) + 1
        records.append(record)

        self._rewrite_all(records)
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
        if notes:
            target.notes = (target.notes + "\n" + notes).strip()

        # Rewrite all records cleanly
        self._rewrite_all(records)
        return True

    def _rewrite_all(self, records: List[ApplicationRecord]) -> None:
        """Rewrites the full CSV while preserving header formatting."""
        with open(self.csv_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Row 0: spacer
            writer.writerow([""] * len(CSV_HEADERS))
            # Row 1: header names
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

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculates tracking dashboard metrics."""
        records = self.load_records()
        total = len(records)
        status_counts: Dict[str, int] = {}
        for r in records:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1

        sent_count = sum(
            1 for r in records if "Sent" in r.status or r.resume_sent
        )
        not_pass = status_counts.get("Not Pass?", 0)
        interviews = (
            status_counts.get("Interview Scheduled", 0)
            + status_counts.get("Interview", 0)
        )

        return {
            "total_applications": total,
            "resumes_sent": sent_count,
            "not_pass": not_pass,
            "interviewing": interviews,
            "status_breakdown": status_counts,
        }
