"""JobThai platform adapter.
"""

from src.services.platforms.base_platform import BasePlatform


class JobThaiPlatform(BasePlatform):
    def __init__(self):
        super().__init__(
            platform_id="jobthai",
            name="JobThai",
            base_url="https://www.jobthai.com",
            search_url_template="https://www.jobthai.com/th/jobs?keyword={keywords}",
            color="#e11d48",
            tag="High Volume Thai Employers",
        )

    def get_instructions(self) -> str:
        return (
            "1. Search openings on JobThai.\n"
            "2. Supports 'Apply Now' via JobThai account or 'Send Email Application'.\n"
            "3. If sending via email, copy the generated HR letter and attach Kwankhao_Sivasomboon_Resume.pdf.\n"
            "4. Fill Expected Salary: 40,000 - 45,000 บาท.\n"
            "5. Record application in CSV."
        )
