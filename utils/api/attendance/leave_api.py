from utils.api.base_api import post, get, put


def apply_leave(
    user: str,
    start_date: str,
    end_date: str,
    leave_reason_type: int,
    subject: str,
    mail: str,
    start_session: str = "Full Day",
    end_session: str = "Full Day",
    work_delegation_id: int = 0
) -> dict:
    return post("Hrlense_Leave", user=user, payload={
        "startSession": start_session,
        "endSession": end_session,
        "start_Date": start_date,
        "end_Date": end_date,
        "leave_Reason_Type": leave_reason_type,
        "mail": mail,
        "subject": subject,
        "work_Delegation_Id": work_delegation_id
    })


def get_pending_leaves(approver: str = "vivek", from_date: str = None) -> list:
    import json
    filter_val = json.dumps({"date": from_date}) if from_date else "{}"
    result = get("Hrlense_Leave/LeaveRequests", user=approver, params={
        "lazyParams": json.dumps({"first": 0, "rows": 100, "page": 0, "sortField": "", "sortOrder": 1}),
        "filter": filter_val,
        "search": ""
    })
    return result.get("data", [])


def get_my_leaves(user: str, status: str = "pending") -> list:
    return get("Hrlense_Leave/leaves", user=user, params={"status": status})


def approve_leave(leave_id: int, approver: str = "vivek") -> dict:
    return put("Hrlense_Leave/leaveApproval", user=approver, payload={
        "id": leave_id,
        "status": True,
        "rejectionReason": ""
    })


def reject_leave(leave_id: int, reason: str, approver: str = "vivek") -> dict:
    return put("Hrlense_Leave/leaveApproval", user=approver, payload={
        "id": leave_id,
        "status": False,
        "rejectionReason": reason
    })
