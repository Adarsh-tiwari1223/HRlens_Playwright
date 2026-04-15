import requests
from core.config import settings

BASE_URL = settings.API_BASE_URL

_token_cache: dict = {}


def get_token(user: str = "admin") -> str:
    if user not in _token_cache:
        creds = settings.USERS[user]
        response = requests.post(f"{BASE_URL}/user/login", json={
            "username": creds["username"],
            "password": creds["password"]
        })
        response.raise_for_status()
        _token_cache[user] = response.json()["token"]
    return _token_cache[user]


def clear_token_cache():
    _token_cache.clear()


def _headers(user: str = "admin") -> dict:
    return {"Authorization": f"Bearer {get_token(user)}"}


def get_weightage_configuration(category: str, business_process: int, department_id: int, cycle_year: int) -> dict:
    params = {
        "category": category,
        "businessProcess": business_process,
        "departmentId": department_id,
        "cycleYear": cycle_year
    }
    return requests.get(f"{BASE_URL}/IncrementSettings/WeightageConfiguration", headers=_headers(), params=params).json()


def get_performance_matrix(category: str, business_process: int, department_id: int, cycle_year: int) -> dict:
    params = {
        "category": category,
        "businessProcess": business_process,
        "departmentId": department_id,
        "cycleYear": cycle_year
    }
    return requests.get(f"{BASE_URL}/IncrementSettings/PerformanceMatrix", headers=_headers(), params=params).json()


def get_increment_slab() -> dict:
    return requests.get(f"{BASE_URL}/IncrementSettings/IncrementSlab", headers=_headers()).json()


def get_business_process() -> dict:
    return requests.get(f"{BASE_URL}/DropDown/businessProcess", headers=_headers()).json()


def get_discipline_setting() -> dict:
    return requests.get(f"{BASE_URL}/IncrementSettings/disciplineSetting", headers=_headers()).json()


def get_employee_category() -> dict:
    return requests.get(f"{BASE_URL}/IncrementSettings/EmployeeCategory", headers=_headers()).json()


def get_efforts(department: str) -> dict:
    return requests.get(f"{BASE_URL}/IncrementSettings/get-all-efforts/{department}", headers=_headers()).json()
