import logging
from utils.api.base_api import get

logger = logging.getLogger(__name__)


def get_companies(user: str = "admin") -> list[dict]:
    """
    GET /Company — fetch all companies/branches.
    Returns a list of dicts, each containing at least:
      { "id": <int>, "name": <str>, ... }
    """
    response = get("Company", user=user)
    # API may return list directly or wrapped in a key
    if isinstance(response, list):
        return response
    return response.get("data", response.get("companies", response.get("result", [])))


def get_company_id_by_name(company_name: str, user: str = "admin") -> int:
    """
    Look up a company by name (case-insensitive) and return its ID.
    Raises ValueError if the company is not found.

    Example:
        company_id = get_company_id_by_name("Originator Informatics")
    """
    companies = get_companies(user=user)
    for company in companies:
        name = company.get("name") or company.get("companyName") or company.get("title") or ""
        if name.strip().lower() == company_name.strip().lower():
            logger.info(f"Found company '{company_name}' → id={company['id']}")
            return int(company["id"])

    available = [
        company.get("name") or company.get("companyName") or company.get("title", "")
        for company in companies
    ]
    raise ValueError(
        f"Company '{company_name}' not found via API. "
        f"Available companies: {available}"
    )


def get_all_company_names(user: str = "admin") -> list[str]:
    """
    Return a flat list of all company names from the API.
    Useful for debugging or validating dropdown options.
    """
    companies = get_companies(user=user)
    return [
        company.get("name") or company.get("companyName") or company.get("title", "")
        for company in companies
    ]


def get_branch_name_api(branch_id: int = None) -> list[str]:
    '''get branch name using branch id or without id as reference'''
    # Note: Assuming the endpoint is 'Branch'. Adjust if different.
    params = {"id": branch_id} if branch_id else None
    response = get("Branch", params=params)
    branches = response.get("data", response.get("records", [])) if isinstance(response, dict) else response
    return [
        branch.get("name") or branch.get("branchName", "")
        for branch in branches
    ]

    