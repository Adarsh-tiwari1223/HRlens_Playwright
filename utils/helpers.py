import json
from pathlib import Path

BASE_DIR = Path("testdata/static").resolve()


def load_test_data(filename: str) -> dict:
    path = (BASE_DIR / Path(filename).name).resolve()
    if not str(path).startswith(str(BASE_DIR)):
        raise ValueError(f"Invalid filename — path traversal detected: {filename}")
    return json.loads(path.read_text(encoding="utf-8"))

from utils.api.base_api import get
from utils.api.company_api import get_companies


def get_employee_full_name_api(employee_code: str = None) -> list[str]:
    '''get employee name using employee code as reference'''
    # Note: Assuming the endpoint is 'Employee'. Adjust if different.
    params = {"employeeCode": employee_code} if employee_code else None
    response = get("Employee", params=params)
    employees = response.get("data", response.get("records", [])) if isinstance(response, dict) else response
    return [
        f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip() or emp.get('fullName', '')
        for emp in employees
    ]

    