import logging
import requests
from core.config import settings
from utils.api.base_api import BaseAPI

logger = logging.getLogger(__name__)


class AssetAPI(BaseAPI):
    """
    API client for HRlens Asset Management operations:
    - POST /api/Asset/assets (Direct Asset Ingestion)
    - GET /api/Asset/categories
    - GET /api/Asset/sub-categories
    - GET /api/branch
    """

    def __init__(self, token: str = None):
        super().__init__(token=token)
        self.base_api_url = settings.API_BASE_URL.rstrip("/")

    def create_asset(self, payload: dict) -> dict:
        """
        Creates an asset directly via POST /api/Asset/assets.
        """
        url = f"{self.base_api_url}/Asset/assets"
        headers = self.get_headers()
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code in [200, 201]:
            try:
                return resp.json()
            except Exception:
                return {"status": "SUCCESS", "status_code": resp.status_code}
        else:
            logger.error(f"Failed to create asset via API: {resp.status_code} - {resp.text}")
            resp.raise_for_status()

    def get_categories(self) -> list:
        """Fetches all categories from backend API."""
        candidates = [
            f"{self.base_api_url}/Category",
            f"{self.base_api_url}/Asset/categories",
            f"{self.base_api_url}/AssetCategory"
        ]
        headers = self.get_headers()
        for url in candidates:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return data.get("data") or data.get("results") or data if isinstance(data, list) else []
            except Exception:
                continue
        return []

    def get_branches(self) -> list:
        """Fetches branches from backend API."""
        url = f"{self.base_api_url}/branch"
        headers = self.get_headers()
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get("data") or data.get("results") or data if isinstance(data, list) else []
        except Exception:
            pass
        return []
