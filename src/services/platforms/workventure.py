"""WorkVenture platform adapter.
"""

from src.services.platforms.base_platform import BasePlatform


class WorkVenturePlatform(BasePlatform):
    def __init__(self):
        super().__init__(
            platform_id="workventure",
            name="WorkVenture",
            base_url="https://www.workventure.com",
            search_url_template="https://www.workventure.com/search?keywords={keywords}",
            color="#7c3aed",
            tag="Modern Tech & Top Companies",
        )

    def get_instructions(self) -> str:
        return (
            "1. Search modern tech companies and startups on WorkVenture.\n"
            "2. WorkVenture is highly culture and tech-driven.\n"
            "3. State your expected salary as 40,000 - 45,000 THB.\n"
            "4. Upload Kwankhao_Sivasomboon_Resume.pdf and submit your cover letter.\n"
            "5. Save entry to history CSV."
        )
