"""LinkedIn platform adapter.
"""

from src.services.platforms.base_platform import BasePlatform


class LinkedInPlatform(BasePlatform):
    def __init__(self):
        super().__init__(
            platform_id="linkedin",
            name="LinkedIn",
            base_url="https://www.linkedin.com/jobs",
            search_url_template="https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}",
            color="#0a66c2",
            tag="Global & Thai Tech",
        )

    def get_instructions(self) -> str:
        return (
            "1. Search or click the direct job link.\n"
            "2. If 'Easy Apply' is available, upload your resume PDF and paste the generated cover letter.\n"
            "3. If directed to company portal (Workday/Lever/Greenhouse), autofill from the quick bar.\n"
            "4. Fill Expected Salary: 40,000 - 45,000 THB.\n"
            "5. Click 'Apply & Log' to record in your history CSV."
        )
