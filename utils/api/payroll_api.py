import json
import time
import logging
import os
from datetime import datetime
from utils.api.base_api import get

logger = logging.getLogger(__name__)

_LAZY = json.dumps({"first": 0, "rows": 1000, "page": 0, "sortField": "", "sortOrder": 1})


def _filter(year: int, month: int, branch_id: int, department_id: int = 0) -> str:
    return json.dumps({"year": year, "month": month, "branchId": branch_id, "departmentId": department_id})


def get_payroll_status(year: int, month: int, branch_id: int,
                       department_id: int = 0, user: str = "admin") -> list:
    """GET /Payroll/status — returns list like [{"status":"generated","count":21},{"status":"pending","count":9}]"""
    return get("Payroll/status", user=user, params={
        "lazyParams": _LAZY,
        "filter": _filter(year, month, branch_id, department_id),
        "search": ""
    })


def get_payroll_list(year: int, month: int, branch_id: int,
                     department_id: int = 0, status: str = None, user: str = "admin") -> dict:
    """GET /Payroll — fetch payroll records. Pass status='pending' to get only pending."""
    f = {"year": year, "month": month, "branchId": branch_id, "departmentId": department_id}
    if status:
        f["status"] = status
    return get("Payroll", user=user, params={
        "lazyParams": _LAZY,
        "filter": json.dumps(f),
        "search": ""
    })


# Large row count to get all records at once (removes pagination)
_RELEASED_PAYROLL_LAZY = json.dumps({"first": 0, "rows": 10000, "page": 0, "sortField": "", "sortOrder": 1})


def get_released_payroll(year: int, month: int, payroll_company_id: int, user: str = "admin") -> dict:
    """
    GET /Payroll — fetch released payroll details.
    Returns all records at once (no pagination) by using rows=10000.
    
    Args:
        year: The year for the payroll (e.g., 2026)
        month: The month for the payroll (e.g., 4)
        payroll_company_id: The payroll company ID (e.g., 7)
        user: The user to authenticate as (default: "admin")
    
    Returns:
        dict: The released payroll data
    """
    filter_params = {"year": year, "month": month, "payrollCompanyId": payroll_company_id}
    return get("Payroll", user=user, params={
        "lazyParams": _RELEASED_PAYROLL_LAZY,
        "filter": json.dumps(filter_params),
        "search": ""
    })


def map_payroll_to_excel(year: int, month: int, payroll_company_id: int,
                           excel_file: str = "testdata/static/Originator-Salary-April'2026.xlsx",
                           sheet_name: str = "APR'26", user: str = "admin") -> dict:
    """
    Map released payroll API data with Excel file data and compare all salary fields.
    
    Args:
        year: The year for the payroll (e.g., 2026)
        month: The month for the payroll (e.g., 4)
        payroll_company_id: The payroll company ID (e.g., 7)
        excel_file: Path to the Excel file
        sheet_name: Sheet name in the Excel file (default: "APR'26")
        user: The user to authenticate as (default: "admin")
    
    Returns:
        dict: Mapping results with comparison data
    """
    import pandas as pd
    import re
    
    # Get released payroll data from API
    api_response = get_released_payroll(year, month, payroll_company_id, user)
    api_data = api_response.get("data", [])
    
    # Read Excel file
    df_excel = pd.read_excel(excel_file, sheet_name=sheet_name, header=5, skiprows=[0])
    
    # API field mapping for each Excel column
    excel_to_api_map = {
        "Emp. Code": "employeeCode",
        "Emp. Name": "employeeName",
        "Basic Salary": "basic",
        "H.R.A. Amt.": "hra",
        "Conv. Amt.": "conveyance_Allowance",
        "INCENTIVE": "incentive",
        "DEDUCTIONS P.F.": "employee_PF",
        "DEDUCTIONS E.S.I.": "esic_Employee",
        "DEDUCTIONS T.D.S.": "tds",
        "Net Payable": "netSalary",
        "Salary Days": "paidDays"
    }

    # Dynamically map Excel column names to their exact column index
    excel_columns = {}
    for col_idx, col_name in enumerate(df_excel.columns):
        col_name_str = str(col_name).strip()
        
        # Pandas appends .1, .2 for duplicate columns (e.g., 'Basic Salary' vs 'Basic Salary.1')
        # We strip the decimal suffix so the later column (earned salary) overwrites the first (fixed salary)
        base_col_name = re.sub(r'\.\d+$', '', col_name_str)
        
        if col_name_str in excel_to_api_map:
            excel_columns[col_name_str] = col_idx
        elif base_col_name in excel_to_api_map:
            excel_columns[base_col_name] = col_idx
            
    # Fallback to catch "Employee Name" if it has slightly different text
    if "Emp. Name" not in excel_columns:
        for col_idx, col_name in enumerate(df_excel.columns):
            if "Name" in str(col_name):
                excel_columns["Emp. Name"] = col_idx
                break

    # Extract Excel data
    excel_data = {}
    for col_name, col_idx in excel_columns.items():
        excel_data[col_name] = df_excel.iloc[:, col_idx].tolist()
    
    # Create API lookup by employee code and employee name
    api_lookup_by_code = {}
    api_lookup_by_name = {}
    for record in api_data:
        emp_code = record.get("employeeCode")
        emp_name = record.get("employeeName")
        
        if emp_code:
            code_str = str(emp_code).strip()
            if code_str.endswith(".0"):
                code_str = code_str[:-2]
            api_lookup_by_code[code_str] = record
            
        if emp_name:
            name_str = str(emp_name).strip().lower()
            api_lookup_by_name[name_str] = record
    
    # Map and compare Excel data with API data
    comparison_results = []
    matched_count = 0
    unmatched_from_excel = []
    matched_api_codes = set()
    
    emp_codes = excel_data.get("Emp. Code", [])
    emp_names = excel_data.get("Emp. Name", [])
    
    for i, emp_code in enumerate(emp_codes):
        emp_name = emp_names[i] if i < len(emp_names) else None
        
        if pd.isna(emp_code) and pd.isna(emp_name):
            continue
        
        emp_code_str = str(emp_code).strip() if not pd.isna(emp_code) else ""
        if emp_code_str.endswith(".0"):
            emp_code_str = emp_code_str[:-2]
            
        emp_name_str = str(emp_name).strip().lower() if not pd.isna(emp_name) else ""
        
        # Try to match by Employee Code first, fallback to Employee Name
        api_record = api_lookup_by_code.get(emp_code_str)
        if not api_record and emp_name_str:
            api_record = api_lookup_by_name.get(emp_name_str)
            
            # If exact match fails, try partial and fuzzy matching
            if not api_record:
                import difflib
                available_names = list(api_lookup_by_name.keys())
                
                # 1. Substring match (e.g., missing middle names)
                for api_name in available_names:
                    if emp_name_str in api_name or api_name in emp_name_str:
                        api_record = api_lookup_by_name[api_name]
                        break
                
                # 2. Fuzzy match for typos (minimum 75% similarity)
                if not api_record:
                    close_matches = difflib.get_close_matches(emp_name_str, available_names, n=1, cutoff=0.75)
                    if close_matches:
                        api_record = api_lookup_by_name[close_matches[0]]
        
        if api_record:
            matched_code = str(api_record.get("employeeCode", "")).strip()
            if matched_code.endswith(".0"):
                matched_code = matched_code[:-2]
            
            if matched_code:
                matched_api_codes.add(matched_code)
                
            matched_count += 1
            
            # Compare each field
            field_comparisons = {}
            for col_name in excel_columns.keys():
                excel_value = excel_data[col_name][i] if i < len(excel_data[col_name]) else None
                api_field = excel_to_api_map[col_name]
                api_value = api_record.get(api_field)
                
                # Handle NaN values
                if pd.isna(excel_value):
                    excel_value = None
                
                field_comparisons[col_name] = {
                    "excel_value": excel_value,
                    "api_value": api_value,
                    "api_field": api_field
                }
                
            comparison_results.append({
                "employeeCode": matched_code,
                "employeeName_excel": emp_name,
                "employeeName_api": api_record.get("employeeName"),
                "fields": field_comparisons
            })
        else:
            unmatched_from_excel.append(emp_code_str or str(emp_name))
            
    unmatched_from_api = [code for code in api_lookup_by_code.keys() if code not in matched_api_codes]
    
    return {
        "matched_count": matched_count,
        "unmatched_from_excel": unmatched_from_excel,
        "unmatched_from_api": unmatched_from_api,
        "comparison_results": comparison_results
    }


def get_branches(user: str = "admin") -> list:
    """GET /Hrlense_Branch — fetch all branches."""
    resp = get("Hrlense_Branch", user=user, params={
        "lazyParams": _LAZY,
        "search": ""
    })
    return resp.get("data", []) if isinstance(resp, dict) else resp


def find_branch_id(branch_name: str, company_name: str = None, user: str = "admin") -> int:
    """
    Look up branch ID by branch name (case-insensitive).
    If multiple branches share the same name, pass company_name to narrow it down.
    Raises ValueError with a list of matches if ambiguous.
    """
    branches = get_branches(user=user)
    matches = [
        b for b in branches
        if b["branch_Name"].strip().lower() == branch_name.strip().lower()
    ]
    if company_name:
        matches = [
            b for b in matches
            if b["company_Name"].strip().lower() == company_name.strip().lower()
        ]
    if len(matches) == 1:
        return matches[0]["id"]
    if len(matches) == 0:
        available = sorted({b["branch_Name"] for b in branches})
        msg = f"Branch '{branch_name}'"
        if company_name:
            msg += f" for company '{company_name}'"
        msg += f" not found. Available branches: {available}"
        raise ValueError(msg)
    # Ambiguous — show options
    options = "\n".join(
        f"  id={b['id']}  branch='{b['branch_Name']}'  company='{b['company_Name']}'"
        for b in matches
    )
    raise ValueError(
        f"Multiple branches named '{branch_name}'. Pass company_name to narrow down:\n{options}"
    )


def get_employee_detail(employee_id: int, user: str = "admin") -> dict:
    """GET /Hrlense_Employee/employeerDetail — fetch configured salary for an employee."""
    return get("Hrlense_Employee/employeerDetail", user=user, params={"employeeId": employee_id})


def get_bank_detail(employee_id: int, user: str = "admin") -> dict:
    """GET /Hrlense_Employee/bankAccountDetail — fetch bank details for an employee."""
    return get("Hrlense_Employee/bankAccountDetail", user=user, params={"employeeId": employee_id})


def get_balance_leave(employee_id: int, user: str = "admin") -> dict:
    """GET /Hrlense_BalanceLeave — fetch leave balance for an employee."""
    return get("Hrlense_BalanceLeave", user=user, params={
        "lazyParams": json.dumps({"first": 0, "rows": 20, "page": 0, "sortField": "", "sortOrder": 1}),
        "filter": json.dumps({"employeeId": employee_id}),
        "search": ""
    })


def wait_for_payroll_complete(year: int, month: int, branch_id: int,
                               department_id: int = 0, user: str = "admin",
                               timeout: int = 300, interval: int = 10) -> list:
    """
    Poll GET /Payroll/status until pending count == 0.
    Response format: [{"status": "generated", "count": 21}, {"status": "pending", "count": 9}]
    Returns the final status list.
    """
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        status_list = get_payroll_status(year, month, branch_id, department_id, user)
        pending_count = next(
            (s["count"] for s in status_list if s.get("status") == "pending"), 0
        )
        generated_count = next(
            (s["count"] for s in status_list if s.get("status") == "generated"), 0
        )
        logger.info(
            "Payroll status poll attempt %d: generated=%d pending=%d",
            attempt, generated_count, pending_count
        )
        if pending_count == 0:
            logger.info("Payroll generation complete after %d poll(s)", attempt)
            return status_list
        time.sleep(interval)

    raise TimeoutError(
        f"Payroll not complete after {timeout}s "
        f"(year={year}, month={month}, branchId={branch_id})"
    )


def flag_payroll_generated(year: int, month: int, branch_id: int,
                           branch_name: str = None, company_name: str = None,
                           department_id: int = 0, user: str = "admin") -> str:
    """
    Check payroll status and create a flag file if payroll is fully generated.
    Returns the path to the flag file if created, otherwise None.
    """
    status_list = get_payroll_status(year, month, branch_id, department_id, user)
    pending_count = next(
        (s["count"] for s in status_list if s.get("status") == "pending"), 0
    )

    if pending_count == 0:
        # Create flag file with current date
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(logs_dir, exist_ok=True)

        current_date = datetime.now().strftime("%Y-%m-%d")
        flag_file_path = os.path.join(logs_dir, "payroll_generated_flag.txt")

        with open(flag_file_path, "w") as f:
            f.write(f"Payroll fully generated on {current_date}\n")
            f.write(f"Year: {year}, Month: {month}, Branch ID: {branch_id}\n")
            if branch_name:
                f.write(f"Branch Name: {branch_name}\n")
            if company_name:
                f.write(f"Company Name: {company_name}\n")

        logger.info(f"Payroll flag file created: {flag_file_path}")
        return flag_file_path

    return None
