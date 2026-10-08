"""JobTopGun platform adapter.
"""

from src.services.platforms.base_platform import BasePlatform


class JobTopGunPlatform(BasePlatform):
    def __init__(self):
        super().__init__(
            platform_id="jobtopgun",
            name="JobTopGun",
            base_url="https://www.jobtopgun.com",
            search_url_template="https://www.jobtopgun.com/search?keyword={keywords}",
            color="#059669",
            tag="Professional & Engineering Jobs",
        )

    def get_instructions(self) -> str:
        return (
            "1. Search engineering & AI positions on JobTopGun / Super Resume.\n"
            "2. Utilize the Super Resume or direct apply feature.\n"
            "3. Expected Salary field: enter 40,000 - 45,000 THB.\n"
            "4. Attach resume and paste cover letter in additional comments.\n"
            "5. Save entry to history CSV."
        )
