"""Unit tests for the History Tracker service.
"""

import shutil
from src.config import CSV_HISTORY_PATH
from src.models import ApplicationRecord
from src.services.history_tracker import HistoryTracker


def test_load_existing_records():
    tracker = HistoryTracker()
    records = tracker.load_records()
    assert len(records) >= 20  # User's CSV already has 27 records
    first = records[0]
    assert first.company == "SCB Tech X"
    assert first.job_position == "Software Engineer"


def test_add_and_update_record(tmp_path):
    # Test on a temporary copy to preserve real user CSV
    test_csv = tmp_path / "test_applications.csv"
    shutil.copyfile(CSV_HISTORY_PATH, test_csv)

    tracker = HistoryTracker(csv_path=test_csv)
    initial_count = len(tracker.load_records())

    # Add record
    new_record = ApplicationRecord(
        company="TechCorp Bangkok",
        job_position="AI Product Engineer",
        link="https://example.com/job/123",
        salary="40,000 - 45,000 THB",
        status="Resume Sent",
    )
    added = tracker.add_record(new_record)
    assert added.id == initial_count + 1

    records_after = tracker.load_records()
    assert len(records_after) == initial_count + 1
    assert records_after[-1].company == "TechCorp Bangkok"

    # Update status
    updated = tracker.update_record_status(added.id, "Interview Scheduled")
    assert updated is True

    records_updated = tracker.load_records()
    assert records_updated[-1].status == "Interview Scheduled"
