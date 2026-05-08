import json
import time
import logging
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


def get_branches(user: str = "admin") -> list:
    """GET /Hrlense_Branch — returns all branches with company info."""
    return get("Hrlense_Branch", user=user)


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
        raise ValueError(f"Branch '{branch_name}' not found. Available: {available}")
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
