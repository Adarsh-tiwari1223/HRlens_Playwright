"""
HRlens Portal — Static Attendance Settings & Hierarchy Rules.
Contains:
1. DEFAULT_ATTENDANCE_SETTING: Global fallback configuration used when no explicit
   (Company, Branch, Department) record exists in Attendance Setting Master.
2. BRANCH_SHIFTS: Standard shift definitions mapped to departments/roles.
"""

DEFAULT_ATTENDANCE_SETTING = {
    "totalWorkingHour": 8.0,
    "halfDayTime": 4.0,
    "lateMinute": 5,           # 5 minutes late grace
    "lateGraceMinutes": 5,     # Alias for frontend field name
    "graceHour": 2.0,          # 2 hours grace after shift end
    "graceHourAfterShiftEnd": 2.0,
    "shortLeaveFrom": 6.0,
    "shortLeaveTo": 8.0,
    "shortLeaveCountForHalfDay": 3,
    "status": True,
}

# Branch shift schedules (e.g. Varanasi shifts)
BRANCH_SHIFTS = {
    "Varanasi": {
        "Shift_A": {
            "name": "Shift A",
            "start_time": "14:00:00",   # 2:00 PM
            "end_time": "23:00:00",     # 11:00 PM
            "departments": ["Developer"],
        },
        "Shift_B": {
            "name": "Shift B",
            "start_time": "18:30:00",   # 6:30 PM
            "end_time": "03:30:00",     # 3:30 AM (Next Day)
            "departments": ["Sales", "Recruiter", "Accounts"],
        },
    }
}


def resolve_attendance_configuration(
    company_id: int | None,
    branch_id: int | None,
    department_id: int | None,
    master_records: list[dict]
) -> tuple[dict, str]:
    """
    Resolves the effective attendance setting according to the business hierarchy:
    1. If a matching (company, branch, department) record exists -> returns (record, "CONFIGURED")
    2. Otherwise -> returns (DEFAULT_ATTENDANCE_SETTING, "DEFAULT")
    """
    for rec in master_records:
        cid = rec.get("companyId") or rec.get("company_Id")
        bid = rec.get("branchId") or rec.get("branch_Id")
        did = rec.get("departmentId") or rec.get("department_Id")

        if cid == company_id and bid == branch_id and did == department_id:
            return rec, "CONFIGURED"

    return DEFAULT_ATTENDANCE_SETTING.copy(), "DEFAULT"


def get_attendance_fetch_delay_hours(config: dict) -> float:
    """
    Returns the grace hours after shift end when attendance is fetched/processed:
    - Configured: returns float(config['graceHour'] or config['graceHourAfterShiftEnd'])
    - Default: returns 2.0 hours
    """
    return float(config.get("graceHourAfterShiftEnd") or config.get("graceHour") or 2.0)

