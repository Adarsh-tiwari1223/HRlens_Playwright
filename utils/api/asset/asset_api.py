"""
Asset Management API Query Utility (HRlens Portal).

Provides high-speed, read-only data queries for:
- Asset Master Categories       (GET /api/AssesstsMaster/categories)
- Asset Master Sub-Categories   (GET /api/AssesstsMaster/subCategory)
- Asset Master Vendors          (GET /api/AssesstsMaster/vendors)
- Branch Stock Asset Inventory  (GET /api/Asset/stock-by-branch/assets)

Used by UI test suites and seeding scripts to query current database state.
"""

import logging
import requests
from core.config import settings

logger = logging.getLogger(__name__)

_token_cache: dict = {}


# ============================================================================
# AUTHENTICATION & HEADERS
# ============================================================================

def get_api_token(user: str = "admin") -> str:
    """Authenticates via /user/login and returns cached Bearer JWT token."""
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


def get_auth_headers(user: str = "admin") -> dict:
    """Returns standard authorization headers with Bearer token."""
    token = get_api_token(user)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


# ============================================================================
# READ-ONLY MASTER DATA QUERIES
# ============================================================================

def get_categories(user: str = "admin") -> requests.Response:
    """
    GET /api/AssesstsMaster/categories
    Returns requests.Response containing all active asset categories.
    """
    url = f"{settings.API_BASE_URL}/AssesstsMaster/categories"
    return requests.get(url, headers=get_auth_headers(user), timeout=15)


def get_subcategories(user: str = "admin") -> requests.Response:
    """
    GET /api/AssesstsMaster/subCategory
    Returns requests.Response containing all active asset subcategories.
    """
    url = f"{settings.API_BASE_URL}/AssesstsMaster/subCategory"
    return requests.get(url, headers=get_auth_headers(user), timeout=15)


def get_vendors(user: str = "admin") -> requests.Response:
    """
    GET /api/AssesstsMaster/vendors
    Returns requests.Response containing all registered asset vendors.
    """
    url = f"{settings.API_BASE_URL}/AssesstsMaster/vendors"
    resp = requests.get(url, headers=get_auth_headers(user), timeout=15)
    if resp.status_code == 404:
        resp = requests.get(f"{settings.API_BASE_URL}/AssesstsMaster/vendor", headers=get_auth_headers(user), timeout=15)
    return resp


# ============================================================================
# BRANCH STOCK & INVENTORY QUERIES
# ============================================================================

def get_stock_by_branch_assets(
    branch_id: int = 1,
    category_id: int = 1,
    status: str = "Available",
    first: int = 0,
    rows: int = 2000,
    user: str = "admin"
) -> list:
    """
    GET /api/Asset/stock-by-branch/assets
    Fetches stock asset records by branch, category, and status.
    Used by UI scoping validation tests to verify database inventory counts.
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
        resp = requests.get(url, params=params, headers=get_auth_headers(user), timeout=15)
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
