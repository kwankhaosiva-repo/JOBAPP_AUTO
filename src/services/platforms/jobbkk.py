"""JobBKK platform adapter.
"""

from src.services.platforms.base_platform import BasePlatform


class JobBKKPlatform(BasePlatform):
    def __init__(self):
        super().__init__(
            platform_id="jobbkk",
            name="JobBKK",
            base_url="https://www.jobbkk.com",
            search_url_template="https://www.jobbkk.com/jobs/search?keyword={keywords}",
            color="#2563eb",
            tag="Bangkok Tech & Enterprise",
        )

    def get_instructions(self) -> str:
        return (
            "1. Browse openings on JobBKK.\n"
            "2. Fill in the JobBKK quick application form.\n"
            "3. State your expected salary as 40,000 - 45,000 THB.\n"
            "4. Upload Kwankhao_Sivasomboon_Resume.pdf.\n"
            "5. Save entry to history CSV."
        )
