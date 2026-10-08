"""Job description parser and fetcher service.
"""

from typing import Dict, Optional
import re
import requests


class ScraperService:
    """Helper to fetch and parse job descriptions from URLs or text."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

    def fetch_page_text(self, url: str) -> Optional[str]:
        """Fetches HTML page text safely."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                # Remove script and style tags using regex to avoid external dependency issues
                clean = re.sub(r"<(script|style).*?</\1>", "", resp.text, flags=re.DOTALL | re.IGNORECASE)
                clean = re.sub(r"<[^>]+>", " ", clean)
                clean = re.sub(r"\s+", " ", clean).strip()
                return clean
        except Exception:
            pass
        return None

    def quick_parse_metadata(self, text: str) -> Dict[str, str]:
        """Infers basic role keywords or location if possible."""
        metadata = {"suggested_role": "", "suggested_location": "Bangkok, Thailand"}
        text_lower = text.lower()

        roles = [
            ("AI Engineer", ["ai engineer", "artificial intelligence engineer"]),
            ("AI Product Engineer", ["ai product engineer", "ai product"]),
            ("Software Engineer", ["software engineer", "software developer", "backend engineer"]),
            ("Data Scientist", ["data scientist"]),
            ("Machine Learning Engineer", ["machine learning engineer", "ml engineer"]),
        ]

        for role_name, kws in roles:
            if any(k in text_lower for k in kws):
                metadata["suggested_role"] = role_name
                break

        return metadata
