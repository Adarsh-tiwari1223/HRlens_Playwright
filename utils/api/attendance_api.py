from utils.api.base_api import get


import json
from utils.api.base_api import get


def get_attendance_summary(from_date: str, to_date: str, user: str = "admin") -> list:
    """GET /Hrlense_Attendance/employee-attendance-summary — returns all records."""
    resp = get("Hrlense_Attendance/employee-attendance-summary", user=user, params={
        "name": "",
        "from": from_date,
        "to": to_date,
        "filters": "{}",
        "lazyParams": json.dumps({"first": 0, "rows": 9999, "page": 0, "sortField": "", "sortOrder": 1}),
    })
    return resp.get("records", [])
