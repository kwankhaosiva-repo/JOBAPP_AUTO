"""Platform adapters package.
"""

from src.services.platforms.base_platform import BasePlatform
from src.services.platforms.linkedin import LinkedInPlatform
from src.services.platforms.jobsdb import JobsDBPlatform
from src.services.platforms.jobthai import JobThaiPlatform
from src.services.platforms.jobbkk import JobBKKPlatform
from src.services.platforms.jobtopgun import JobTopGunPlatform
from src.services.platforms.workventure import WorkVenturePlatform
from src.services.platforms.platform_manager import PlatformManager

__all__ = [
    "BasePlatform",
    "LinkedInPlatform",
    "JobsDBPlatform",
    "JobThaiPlatform",
    "JobBKKPlatform",
    "JobTopGunPlatform",
    "WorkVenturePlatform",
    "PlatformManager",
]
