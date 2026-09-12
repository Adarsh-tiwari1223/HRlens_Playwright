import json
import logging
from utils.api.base_api import get

logger = logging.getLogger(__name__)


def get_absence_case_list(
    rows: int = 500,
    search: str = "",
    status: str = "",
    user: str = "admin"
) -> list[dict]:
    """
    GET /api/AbsenceCase/list
    Retrieves absence case list via pure API call.
    """
    lazy_params = json.dumps({
        "first": 0,
        "rows": rows,
        "page": 0,
        "sortField": "",
        "sortOrder": 1
    })
    
    params = {
        "lazyParams": lazy_params,
        "search": search,
        "status": status
    }
    
    try:
        resp = get("AbsenceCase/list", user=user, params=params)
        if isinstance(resp, list):
            return resp
        elif isinstance(resp, dict):
            if "data" in resp:
                if isinstance(resp["data"], list):
                    return resp["data"]
                if isinstance(resp["data"], dict):
                    return resp["data"].get("rows") or resp["data"].get("data") or []
            if "rows" in resp:
                return resp["rows"]
        return []
    except Exception as e:
        logger.error(f"Error fetching AbsenceCase/list: {e}")
        return []


def get_absence_case_by_id(case_id: int, user: str = "admin") -> dict:
    """
    GET /api/AbsenceCase/{id}
    Retrieves single absence case details via pure API call.
    """
    try:
        resp = get(f"AbsenceCase/{case_id}", user=user)
        return resp if isinstance(resp, dict) else {}
    except Exception as e:
        logger.error(f"Error fetching AbsenceCase/{case_id}: {e}")
        return {}
