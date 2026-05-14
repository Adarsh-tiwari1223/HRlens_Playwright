from utils.api.base_api import post, get, put

def apply_remote(
    user: str,
    start_date: str,
    end_date: str,
    reason: str,
    subject: str,
    mail: str,
    approval_name: str = "",
    start_session: str = "Full Day",
    end_session: str = "Full Day",
    work_delegation_id: int = 0
) -> dict:

    return post("Remote", user=user,payload = {
        "startDate": start_date,
        "endDate": end_date,
        "reason": reason,
        "subject": subject,
        "mail": mail,
        "approvalName": approval_name,
        "startSession": start_session,
        "endSession": end_session,
        "workDelegationId": work_delegation_id
    })

def get_pending_remotes(approver: str = "vivek") -> list:
    result = get("Remote/remote", user=approver, params={"status": "pending"})
    print(result)
    return result
