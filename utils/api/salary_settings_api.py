"""
Salary Calculation Settings API Client for HRlens Portal.
Fetches configured minimum basic, minimum gross salary, HRA %, Basic %, PF thresholds, etc.
"""

import json
import logging
import random
import requests
from typing import Dict, Any, List
from core.config import settings

logger = logging.getLogger(__name__)


def _get_api_token(user: str = "admin") -> str:
    """Gets API JWT bearer token via requests without touching Playwright sync state."""
    creds = settings.USERS.get(user, settings.USERS.get("admin", {}))
    login_url = f"{settings.API_BASE_URL}/user/login"
    payload = {
        "email": creds["username"],
        "user": creds["username"],
        "password": creds["password"]
    }
    try:
        resp = requests.post(login_url, json=payload, timeout=15)
        if resp.ok:
            return resp.json().get("token", "")
    except Exception as ex:
        logger.warning(f"Failed to fetch API token via requests: {ex}")
    return ""


def get_salary_calculation_settings(user: str = "admin") -> List[Dict[str, Any]]:
    """
    GET /SalaryCalculationSettings — fetch all salary calculation setting records from API.
    Returns list of dicts containing salary settings parameters.
    """
    params = {
        "first": 0,
        "rows": 1000,
        "sortOrder": 1
    }
    url = f"{settings.API_BASE_URL}/SalaryCalculationSettings"
    token = _get_api_token(user)
    hdrs = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        resp = requests.get(url, headers=hdrs, params=params, timeout=30)
        if resp.ok:
            data = resp.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("data", data.get("records", data.get("result", [])))
    except Exception as ex:
        logger.warning(f"Error fetching SalaryCalculationSettings via API: {ex}")

    return []


def get_salary_settings_for_company(company_name: str = "", branch_name: str = "", employment_type: str = "Employee", user: str = "admin") -> Dict[str, Any]:
    """
    Fetch specific salary calculation setting for a company, branch, and employment type from API.
    Returns a dict with key threshold parameters:
      - configured_minimum_basic_salary (min_Basic)
      - configured_minimum_gross_salary (min_Gross_Salary)
      - basic_percentage (basic_Percentage)
      - hra_percentage (hrA_Percentage)
    """
    records = get_salary_calculation_settings(user=user)
    logger.info(f"[API] Fetched {len(records)} SalaryCalculationSettings records.")

    matched_record = None
    for rec in records:
        rec_comp = rec.get("company_Name") or rec.get("companyName") or rec.get("company") or ""
        rec_branch = rec.get("branch_Name") or rec.get("branchName") or rec.get("branch") or ""
        rec_emp_type = (rec.get("employement_Type") or rec.get("employmentType") or "").upper()
        rec_pay_type = (rec.get("intern_Payment_Type") or "").upper()
        min_b = float(rec.get("min_Basic") or rec.get("minBasic") or 0.0)

        # Exclude INTERN and UNPAID records strictly
        if rec_emp_type == "INTERN" or rec_pay_type == "UNPAID":
            continue

        comp_match = not company_name or company_name.lower() in rec_comp.lower()
        branch_match = not branch_name or branch_name.lower() in rec_branch.lower()

        if comp_match and branch_match and min_b > 0:
            matched_record = rec
            break

    if not matched_record:
        # Fallback to first EMPLOYEE record with min_Basic > 0 (excluding INTERN / UNPAID)
        for rec in records:
            rec_emp_type = (rec.get("employement_Type") or rec.get("employmentType") or "").upper()
            rec_pay_type = (rec.get("intern_Payment_Type") or "").upper()
            min_b = float(rec.get("min_Basic") or rec.get("minBasic") or 0.0)
            if rec_emp_type == "EMPLOYEE" and rec_pay_type != "UNPAID" and min_b > 0:
                matched_record = rec
                break

    if not matched_record:
        # Defaults if API returns empty
        return {
            "configured_minimum_basic_salary": 16000.0,
            "configured_minimum_gross_salary": 15000.0,
            "basic_percentage": 50.0,
            "hra_percentage": 40.0
        }

    comp_name = matched_record.get("company_Name") or matched_record.get("companyName") or matched_record.get("company") or "N/A"
    br_name = matched_record.get("branch_Name") or matched_record.get("branchName") or matched_record.get("branch") or "N/A"
    dept_name = matched_record.get("department_Name") or matched_record.get("departmentName") or matched_record.get("department") or "N/A"
    emp_type = matched_record.get("employement_Type") or matched_record.get("employmentType") or "N/A"

    min_basic = float(
        matched_record.get("min_Basic") or matched_record.get("minBasic") or matched_record.get("minimumBasic") or 16000.0
    )
    min_gross = float(
        matched_record.get("min_Gross_Salary") or matched_record.get("minGrossSalary") or matched_record.get("minimumGrossSalary") or 15000.0
    )
    basic_pct = float(
        matched_record.get("basic_Percentage") or matched_record.get("basicPercentage") or 50.0
    )
    hra_pct = float(
        matched_record.get("hrA_Percentage") or matched_record.get("hraPercentage") or 40.0
    )

    logger.info(
        f"[API MATCH] Setting exists for Company: '{comp_name}' | Branch: '{br_name}' | "
        f"Department: '{dept_name}' | Employment Type: '{emp_type}' -> "
        f"min_Basic={min_basic}, min_Gross_Salary={min_gross}"
    )

    return {
        "company_name": comp_name,
        "branch_name": br_name,
        "department_name": dept_name,
        "employment_type": emp_type,
        "configured_minimum_basic_salary": min_basic,
        "configured_minimum_gross_salary": min_gross,
        "basic_percentage": basic_pct,
        "hra_percentage": hra_pct,
        "raw_record": matched_record
    }


def update_salary_calculation_setting(setting_id: int, payload: Dict[str, Any], user: str = "admin") -> bool:
    """
    PUT /SalaryCalculationSettings/{setting_id} — Update salary calculation setting on stage.
    """
    url = f"{settings.API_BASE_URL}/SalaryCalculationSettings/{setting_id}"
    token = _get_api_token(user)
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    } if token else {"Content-Type": "application/json"}

    try:
        resp = requests.put(url, headers=hdrs, json=payload, timeout=30)
        if resp.ok or resp.status_code in [200, 201, 204]:
            logger.info(f"[API PUT SUCCESS] Updated SalaryCalculationSettings id={setting_id}")
            return True
        else:
            logger.warning(f"[API PUT FAILED] Status {resp.status_code} for id={setting_id}: {resp.text}")
    except Exception as ex:
        logger.warning(f"Error updating SalaryCalculationSettings id={setting_id}: {ex}")

    return False


def update_company_salary_settings(
    company_name: str,
    min_gross_salary: float,
    min_basic_salary: float = None,
    user: str = "admin"
) -> Dict[str, Any]:
    """
    Flow: GET SalaryCalculationSettings -> find record for company_name -> PUT updated min_Gross_Salary (and optional min_Basic).
    Works for companies like 'TEK Inspirations LLC', 'Jobvritta Inc', 'ABS Staffing', etc.
    """
    records = get_salary_calculation_settings(user=user)
    target_rec = None
    for rec in records:
        comp = rec.get("company_Name") or rec.get("companyName") or ""
        emp_type = (rec.get("employement_Type") or "").upper()
        pay_type = (rec.get("intern_Payment_Type") or "").upper()
        if emp_type == "INTERN" or pay_type == "UNPAID":
            continue
        if company_name.lower() in comp.lower() and emp_type == "EMPLOYEE":
            target_rec = rec
            break

    if not target_rec:
        for rec in records:
            comp = rec.get("company_Name") or rec.get("companyName") or ""
            emp_type = (rec.get("employement_Type") or "").upper()
            pay_type = (rec.get("intern_Payment_Type") or "").upper()
            if emp_type == "INTERN" or pay_type == "UNPAID":
                continue
            if company_name.lower() in comp.lower():
                target_rec = rec
                break

    if not target_rec:
        logger.warning(f"No existing record found for company '{company_name}' to update.")
        return {}

    setting_id = target_rec.get("id")
    payload = dict(target_rec)
    payload["min_Gross_Salary"] = min_gross_salary
    if min_basic_salary is not None:
        payload["min_Basic"] = min_basic_salary

    success = update_salary_calculation_setting(setting_id, payload, user=user)
    if success:
        return get_salary_settings_for_company(company_name=company_name, user=user)
    return target_rec


def get_top_10_salary_settings(user: str = "admin") -> List[Dict[str, Any]]:
    """
    1. GET /SalaryCalculationSettings via API (rows=1000).
    2. Filter records: strictly require min_Basic > 0 and min_Gross_Salary > 0 for EMPLOYEE type.
    3. Exclude testing / demo company data ('testing', 'test', 'dummy', 'sample', 'demo').
    4. Collect top 10 unique (Company, Branch, Department) non-test setting records.
    5. Return list of up to 10 setting dictionaries.
    """
    records = get_salary_calculation_settings(user=user)
    top_10_company_settings = []
    seen_org_keys = set()
    EXCLUDE_KEYWORDS = ["testing", "test", "dummy", "sample", "demo"]

    for rec in records:
        rec_emp_type = (rec.get("employement_Type") or rec.get("employmentType") or "").upper()
        rec_pay_type = (rec.get("intern_Payment_Type") or "").upper()
        comp = (rec.get("company_Name") or rec.get("companyName") or "").strip()
        br = (rec.get("branch_Name") or rec.get("branchName") or "").strip()
        dept = (rec.get("department_Name") or rec.get("departmentName") or "").strip()
        min_b = float(rec.get("min_Basic") or rec.get("minBasic") or 0.0)
        min_g = float(rec.get("min_Gross_Salary") or rec.get("minGrossSalary") or 0.0)

        is_employee = (rec_emp_type == "EMPLOYEE" and rec_pay_type != "UNPAID")
        is_valid_salary = (min_b > 0 and min_g > 0)
        is_valid_org = (comp != "" and br != "" and dept != "")
        is_non_test_comp = comp and not any(kw in comp.lower() for kw in EXCLUDE_KEYWORDS)

        org_key = (comp.lower(), br.lower(), dept.lower())

        if is_employee and is_valid_salary and is_valid_org and is_non_test_comp and org_key not in seen_org_keys:
            seen_org_keys.add(org_key)
            min_basic = float(rec.get("min_Basic") or rec.get("minBasic") or 16000.0)
            min_gross = float(rec.get("min_Gross_Salary") or rec.get("minGrossSalary") or 15000.0)
            top_10_company_settings.append({
                "id": rec.get("id"),
                "company_name": comp,
                "branch_name": br,
                "department_name": dept,
                "employment_type": rec_emp_type,
                "configured_minimum_basic_salary": min_basic,
                "configured_minimum_gross_salary": min_gross,
                "raw_record": rec
            })
            if len(top_10_company_settings) == 10:
                break

    return top_10_company_settings


def get_random_salary_setting_from_top_10(user: str = "admin") -> Dict[str, Any]:
    """
    Randomly picks 1 setting record from top 10 unique non-test company salary settings.
    """
    settings_list = get_top_10_salary_settings(user=user)
    if not settings_list:
        logger.warning("No non-test EMPLOYEE salary settings with valid min_Basic and min_Gross_Salary found in API!")
        return {
            "configured_minimum_basic_salary": 16000.0,
            "configured_minimum_gross_salary": 15000.0,
            "company_name": "",
            "branch_name": "",
            "department_name": ""
        }

    chosen = random.choice(settings_list)
    logger.info(
        f"[API RANDOM TOP 10] Picked setting → Company: '{chosen['company_name']}' | "
        f"Branch: '{chosen['branch_name']}' | Department: '{chosen['department_name']}' | "
        f"min_Basic={chosen['configured_minimum_basic_salary']}, min_Gross_Salary={chosen['configured_minimum_gross_salary']}"
    )
    return chosen


# Alias for backward compatibility
get_random_salary_setting_from_top_5 = get_random_salary_setting_from_top_10


def search_job_openings_api(search_term: str = "", user: str = "admin") -> List[Dict[str, Any]]:
    """
    GET /JobOpening?lazyParams={"first":0,"rows":1000,"page":0,"sortField":"","sortOrder":1}&status=true&filter={}&search={search_term}
    Queries active job openings matching the search term (e.g. company name, dept) from API.
    """
    url = f"{settings.API_BASE_URL}/JobOpening"
    params = {
        "lazyParams": json.dumps({"first": 0, "rows": 1000, "page": 0, "sortField": "", "sortOrder": 1}),
        "status": "true",
        "filter": "{}",
        "search": search_term
    }
    token = _get_api_token(user)
    hdrs = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        resp = requests.get(url, headers=hdrs, params=params, timeout=30)
        if resp.ok:
            data = resp.json()
            if isinstance(data, dict):
                return data.get("data", [])
            if isinstance(data, list):
                return data
    except Exception as ex:
        logger.warning(f"Error querying GET /JobOpening via API: {ex}")

    return []


def find_matching_job_opening_api(company_name: str, branch_name: str = "", department_name: str = "", user: str = "admin") -> Dict[str, Any] | None:
    """
    Queries GET /JobOpening via API filtered by company_name, branch_name, department_name.
    Returns matched job dict containing 'job_Code', or None if not found.
    """
    records = search_job_openings_api(search_term=company_name, user=user)
    if not records and company_name:
        records = search_job_openings_api(search_term="", user=user)

    for job in records:
        j_comp = job.get("payroll_Company_Name") or job.get("company_Name") or job.get("companyName") or ""
        j_branch = job.get("branch_Name") or job.get("branchName") or ""
        j_dept = job.get("department_Name") or job.get("departmentName") or ""

        comp_match = not company_name or company_name.lower() in j_comp.lower()
        branch_match = not branch_name or branch_name.lower() in j_branch.lower()
        dept_match = not department_name or department_name.lower() in j_dept.lower()

        if comp_match and (branch_match or dept_match or not branch_name):
            return job

    if records:
        return records[0]

    return None
