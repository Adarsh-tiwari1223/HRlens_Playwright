import logging
from utils.api.base_api import get

logger = logging.getLogger(__name__)


def get_directors_api(user: str = "admin") -> list[dict]:
    """
    GET /Director — fetch all assigned directors from backend API.
    Returns list of dict records.
    """
    try:
        response = get("Director", user=user)
        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            return response.get("data", response.get("records", response.get("result", [])))
    except Exception as e:
        logger.warning(f"Failed to fetch directors via API: {e}")
    return []
