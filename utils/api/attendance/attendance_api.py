from utils.api.base_api import get


import json
from utils.api.base_api import get


def get_regularization_approval_setting_api(user: str = "admin") -> dict:
    """GET /Regularization/RegularizationApprovalSetting — returns company, branch, department approval settings."""
    try:
        return get("Regularization/RegularizationApprovalSetting", user=user)
    except Exception:
        return {}


def determine_approval_hierarchy(duration_days: int) -> list[str]:
    """
    Default Approval Hierarchy Matrix:
    - 1 Day: Team Lead -> Manager -> Branch Head
    - 2–7 Days: Manager -> Branch Head
    - > 7 Days: Branch Head
    """
    if duration_days == 1:
        return ["Team Lead", "Manager", "Branch Head"]
    elif 2 <= duration_days <= 7:
        return ["Manager", "Branch Head"]
    else:
        return ["Branch Head"]


def get_dynamic_approval_hierarchy_api(duration_days: int, user: str = "admin") -> list[str]:
    """
    Dynamically fetches Regularization Approval Settings from:
    GET /Regularization/RegularizationApprovalSetting
    and resolves approval hierarchy based on active Company, Branch, & Department configuration.

    Fallback Rule:
    If setting does not exist or is unconfigured -> automatically falls back to ["Branch Head"].
    """
    settings_data = get_regularization_approval_setting_api(user=user)
    if isinstance(settings_data, list) and settings_data:
        for rule in settings_data:
            min_days = rule.get("minDays", 0)
            max_days = rule.get("maxDays", 999)
            if min_days <= duration_days <= max_days:
                hierarchy = rule.get("approvalHierarchy") or rule.get("levels") or rule.get("roles")
                if hierarchy:
                    return hierarchy if isinstance(hierarchy, list) else [str(hierarchy)]

    # Fallback Rule: Automatically falls back to ["Branch Head"] if setting does not exist
    return ["Branch Head"]


def get_attendance_summary(from_date: str, to_date: str, user: str = "admin") -> list:
    """GET /Attendance/summary — returns attendance summary records."""
    try:
        resp = get("Attendance/summary", user=user, params={"fromDate": from_date, "toDate": to_date})
        return resp if isinstance(resp, list) else resp.get("data", [])
    except Exception:
        return []


def get_employee_monthly_attendance_api(month: int = 8, year: int = 2026, user: str = "sanidhy") -> list[dict]:
    """
    GET /Hrlense_Attendance/GetEmployeeMonthlyAttendanceByEmployee?month={month}&year={year}
    Fetches employee monthly attendance records.
    """
    try:
        resp = get(
            "Hrlense_Attendance/GetEmployeeMonthlyAttendanceByEmployee",
            user=user,
            params={"month": str(month), "year": str(year)}
        )
        if isinstance(resp, list):
            return resp
        elif isinstance(resp, dict):
            return resp.get("data") or resp.get("result") or resp.get("attendance") or []
        return []
    except Exception:
        return []


def get_eligible_regularization_dates_api(month: int = 8, year: int = 2026, user: str = "sanidhy") -> list[dict]:
    """
    Business Rule:
    Fetch monthly attendance via API, filter for status != 'Present'.
    Returns list of eligible dates that the employee can regularize:
    [{'day': 3, 'date': '2026-08-03', 'status': 'Absent'}, ...]
    """
    records = get_employee_monthly_attendance_api(month=month, year=year, user=user)
    eligible = []
    for item in records:
        status = str(
            item.get("status") or
            item.get("attendanceStatus") or
            item.get("dayStatus") or
            item.get("punchStatus") or
            ""
        ).strip()

        # Only dates where status is NOT Present are eligible for regularization
        if status and status.upper() not in ["PRESENT"]:
            date_val = item.get("date") or item.get("attendanceDate") or item.get("dayDate") or item.get("currentDate")
            day_val = item.get("day") or item.get("dayNumber")
            day_num = None
            if date_val and isinstance(date_val, str):
                try:
                    clean_d = date_val.split("T")[0]
                    if "-" in clean_d:
                        parts = clean_d.split("-")
                        day_num = int(parts[-1]) if len(parts[0]) == 4 else int(parts[0])
                except Exception:
                    pass

            if day_num is None and day_val:
                try:
                    day_num = int(day_val)
                except Exception:
                    pass

            if day_num:
                eligible.append({
                    "day": day_num,
                    "date": date_val,
                    "status": status,
                    "raw": item
                })
    return eligible
