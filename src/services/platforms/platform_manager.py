"""Platform Manager: Registry and automation orchestrator for all job platforms.
"""

from typing import Dict, List, Optional
import webbrowser
from src.services.platforms.base_platform import BasePlatform
from src.services.platforms.linkedin import LinkedInPlatform
from src.services.platforms.jobsdb import JobsDBPlatform
from src.services.platforms.jobthai import JobThaiPlatform
from src.services.platforms.jobbkk import JobBKKPlatform
from src.services.platforms.jobtopgun import JobTopGunPlatform
from src.services.platforms.workventure import WorkVenturePlatform


class PlatformManager:
    """Coordinates supported job platforms and automation dispatching."""

    def __init__(self):
        self._platforms: Dict[str, BasePlatform] = {
            "linkedin": LinkedInPlatform(),
            "jobsdb": JobsDBPlatform(),
            "jobthai": JobThaiPlatform(),
            "jobbkk": JobBKKPlatform(),
            "jobtopgun": JobTopGunPlatform(),
            "workventure": WorkVenturePlatform(),
        }

    def list_platforms(self) -> List[Dict[str, str]]:
        """Returns details of all registered platforms."""
        return [
            {
                "id": p.platform_id,
                "name": p.name,
                "base_url": p.base_url,
                "color": p.color,
                "tag": p.tag,
                "instructions": p.get_instructions(),
            }
            for p in self._platforms.values()
        ]

    def get_platform(self, platform_id: str) -> Optional[BasePlatform]:
        """Gets platform by its unique ID."""
        return self._platforms.get(platform_id.lower().strip())

    def detect_platform_from_url(self, url: str) -> Optional[BasePlatform]:
        """Infers platform instance based on link domain."""
        url_lower = url.lower()
        if "linkedin.com" in url_lower:
            return self._platforms["linkedin"]
        if "jobsdb.com" in url_lower or "seek" in url_lower:
            return self._platforms["jobsdb"]
        if "jobthai.com" in url_lower:
            return self._platforms["jobthai"]
        if "jobbkk.com" in url_lower:
            return self._platforms["jobbkk"]
        if "jobtopgun.com" in url_lower:
            return self._platforms["jobtopgun"]
        if "workventure.com" in url_lower:
            return self._platforms["workventure"]
        return None

    def launch_browser_url(self, url: str) -> bool:
        """Opens job posting URL directly in the user's default browser."""
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False

    async def launch_with_playwright(self, url: str, headless: bool = False) -> Dict[str, str]:
        """Automated Playwright browser helper for inspection or interaction."""
        from playwright.async_api import async_playwright

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                title = await page.title()
                await browser.close()
                return {"status": "success", "title": title, "url": url}
        except Exception as e:
            return {"status": "error", "message": str(e), "url": url}
