"""JobsDB (SEEK) platform adapter.
"""

import urllib.parse
from src.services.platforms.base_platform import BasePlatform


class JobsDBPlatform(BasePlatform):
    def __init__(self):
        super().__init__(
            platform_id="jobsdb",
            name="JobsDB by SEEK",
            base_url="https://th.jobsdb.com",
            search_url_template="https://th.jobsdb.com/th/search-jobs/{keywords}-in-{location}/1",
            color="#ff6000",
            tag="Top Thai Corporate & Tech",
        )

    def build_search_url(self, keywords: str, location: str = "Bangkok") -> str:
        # JobsDB URL structure: /th/search-jobs/ai-engineer-in-bangkok/1
        kw_slug = keywords.strip().replace(" ", "-").lower()
        loc_slug = location.strip().replace(" ", "-").lower()
        return f"https://th.jobsdb.com/th/search-jobs/{kw_slug}-in-{loc_slug}/1"

    def get_instructions(self) -> str:
        return (
            "1. JobsDB offers 'Quick Apply' with your saved SEEK/JobsDB profile.\n"
            "2. Attach Kwankhao_Sivasomboon_Resume.pdf.\n"
            "3. Paste the generated cover letter in the 'Cover Letter / Additional Information' section.\n"
            "4. For salary, enter 40,000 - 45,000 THB (or 40,000 minimum).\n"
            "5. Save entry to history CSV."
        )
