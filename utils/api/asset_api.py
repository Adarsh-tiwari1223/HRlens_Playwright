import logging
import requests
from core.config import settings

logger = logging.getLogger(__name__)

_token_cache: dict = {}


def get_api_token(user: str = "admin") -> str:
    global _token_cache
    if user not in _token_cache:
        creds = settings.USERS[user]
        login_url = f"{settings.API_BASE_URL}/user/login"
        payload = {
            "email": creds["username"],
            "user": creds["username"],
            "password": creds["password"]
        }
        resp = requests.post(login_url, json=payload, timeout=15)
        if resp.status_code == 200:
            _token_cache[user] = resp.json().get("token", "")
        else:
            logger.error(f"API Login failed: {resp.status_code} - {resp.text}")
    return _token_cache.get(user, "")


def get_stock_by_branch_assets(branch_id: int = 1, category_id: int = 1, status: str = "Available", first: int = 0, rows: int = 2000, user: str = "admin") -> list:
    """
    Fetches stock assets by branch, category and status from:
    GET /api/Asset/stock-by-branch/assets?first=0&rows=2000&branchId={branch_id}&categoryId={category_id}&status={status}
    """
    url = f"{settings.API_BASE_URL}/Asset/stock-by-branch/assets"
    params = {
        "first": first,
        "rows": rows,
        "branchId": branch_id,
        "categoryId": category_id,
        "status": status
    }
    try:
        token = get_api_token(user)
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                return data.get("data") or data.get("results") or data.get("assets") or []
            elif isinstance(data, list):
                return data
        else:
            logger.error(f"Failed to fetch stock-by-branch assets: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Error fetching stock-by-branch assets: {e}")
    return []
