"""Services module.
"""

from src.services.resume_service import ResumeService
from src.services.salary_matcher import SalaryMatcher
from src.services.cover_letter_service import CoverLetterService
from src.services.history_tracker import HistoryTracker
from src.services.platforms.platform_manager import PlatformManager

__all__ = [
    "ResumeService",
    "SalaryMatcher",
    "CoverLetterService",
    "HistoryTracker",
    "PlatformManager",
]
