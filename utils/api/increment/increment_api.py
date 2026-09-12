from utils.api.base_api import get


def get_weightage_configuration(category: str, business_process: int, department_id: int, cycle_year: int) -> dict:
    return get("IncrementSettings/WeightageConfiguration", params={
        "category": category,
        "businessProcess": business_process,
        "departmentId": department_id,
        "cycleYear": cycle_year
    })


def get_performance_matrix(category: str, business_process: int, department_id: int, cycle_year: int) -> dict:
    return get("IncrementSettings/PerformanceMatrix", params={
        "category": category,
        "businessProcess": business_process,
        "departmentId": department_id,
        "cycleYear": cycle_year
    })


def get_increment_slab() -> dict:
    return get("IncrementSettings/IncrementSlab")


def get_business_process() -> dict:
    return get("DropDown/businessProcess")


def get_discipline_setting() -> dict:
    return get("IncrementSettings/disciplineSetting")


def get_employee_category() -> dict:
    return get("IncrementSettings/EmployeeCategory")


def get_efforts(department: str) -> dict:
    return get(f"IncrementSettings/get-all-efforts/{department}")
