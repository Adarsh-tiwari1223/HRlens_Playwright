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


def get_director_document_categories_api(user: str = "admin") -> list[dict]:
    """
    GET /Hrlense_Document_Category
    Returns list of all Director Document Categories (e.g. Category ID 7 = Director Document).
    """
    logger.info("Fetching Director Document Categories via Hrlense_Document_Category API...")
    response = get("Hrlense_Document_Category", user=user)
    if isinstance(response, list):
        return response
    return response.get("data", response.get("result", []))


def get_director_documents_by_category_api(category_id: int = 7, user: str = "admin") -> list[dict]:
    """
    GET /Hrlense_Document_Category/getdocument?category_Id={category_id}
    Returns list of Director Documents (Passport, Aadhaar, PAN, etc.) configured for specified Category ID.
    """
    logger.info(f"Fetching Director Documents for Category ID={category_id} via Hrlense_Document_Category API...")
    endpoint = f"Hrlense_Document_Category/getdocument?category_Id={category_id}"
    response = get(endpoint, user=user)
    if isinstance(response, list):
        return response
    return response.get("data", response.get("result", []))
