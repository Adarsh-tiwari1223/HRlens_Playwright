import requests
import json
import os
import random
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = "https://audit.jobvritta.com/api"
IT_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "testdata", "it_department_employees.json")

def fetch_it_department_employees_from_api(department_id: int = 11) -> list[dict]:
    """
    Queries exact HRlens IT Department API endpoint:
    https://audit.jobvritta.com/api/Hrlense_Employee?department_Id=11&lazyParams={"first":0,"rows":50,"page":0}&filter={}&search=
    """
    url = f"{API_BASE_URL}/Hrlense_Employee?department_Id={department_id}&lazyParams=%7B%22first%22%3A0%2C%22rows%22%3A50%2C%22page%22%3A0%2C%22sortField%22%3A%22%22%2C%22sortOrder%22%3A1%7D&filter=%7B%7D&search="
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            body = res.json()
            items = body.get("employee") or body.get("data") or body.get("results") or (body if isinstance(body, list) else [])
            if isinstance(items, dict):
                items = items.get("rows") or items.get("data") or []
            
            parsed_list = []
            for item in items:
                name = item.get("name") or item.get("employee_Name") or item.get("full_Name")
                email = item.get("email") or item.get("official_Email")
                emp_code = item.get("empCode") or item.get("emp_Code")
                branch = item.get("branch") or "Varanasi"
                desig = item.get("designation") or "IT Support"
                if name:
                    parsed_list.append({
                        "id": item.get("id"),
                        "name": name,
                        "email": email or f"{name.lower().replace(' ', '.')}@tekinspirations.com",
                        "empCode": emp_code,
                        "branch": branch,
                        "designation": desig,
                        "department_Id": department_id,
                        "status": item.get("status", "Active")
                    })
            if parsed_list:
                logger.info(f"[IT EMP API SUCCESS] Fetched {len(parsed_list)} IT department employees (Dept ID: {department_id})")
                return parsed_list
    except Exception as ex:
        logger.warning(f"IT Department API fetch note: {ex}")

    return []

def load_it_employees() -> list[dict]:
    """Loads all 13 IT department employees from API or JSON cache."""
    # 1. Attempt API fetch
    api_emps = fetch_it_department_employees_from_api(department_id=11)
    if api_emps:
        return api_emps

    # 2. Attempt IT JSON cache
    if os.path.exists(IT_JSON_PATH):
        try:
            with open(IT_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and isinstance(data, list):
                    return data
        except Exception as ex:
            logger.warning(f"Failed to read {IT_JSON_PATH}: {ex}")

    return []

def get_random_dynamic_employee(branch: str = None) -> dict:
    """Returns a random dynamic IT Department employee, optionally filtered by branch (e.g. Varanasi, Agra, Meerut, Noida, Lucknow, Jaipur)."""
    emps = load_it_employees()
    if branch:
        filtered = [e for e in emps if branch.lower() in e.get("branch", "").lower()]
        if filtered:
            return random.choice(filtered)
    return random.choice(emps)
