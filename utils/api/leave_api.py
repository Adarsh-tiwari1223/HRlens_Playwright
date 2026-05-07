from utils.api.base_api import post


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
