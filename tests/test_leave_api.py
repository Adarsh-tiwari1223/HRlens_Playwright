import pytest
import requests
from datetime import date, timedelta
from core.config import settings
from utils.api.base_api import headers
from utils.api.leave_api import apply_leave, reject_leave, get_pending_leaves, get_my_leaves


@pytest.fixture(scope="module")
def leave_dates():
    return "2026-04-04", "2026-04-04"


@pytest.fixture(scope="module")
def back_leave_dates():
    back = date.today() - timedelta(days=settings.LEAVE_BACK_DATE_OFFSET)
    return back.strftime("%Y-%m-%d"), back.strftime("%Y-%m-%d")


@pytest.fixture(scope="module")
def leave_response(leave_dates):
    start_date, end_date = leave_dates
    return apply_leave(
        user=settings.EMPLOYEE_USER,
        start_date=start_date,
        end_date=end_date,
        leave_reason_type=14,
        subject="Automated Leave Request",
        mail="<p>Automated test leave request</p>"
    )


@pytest.fixture(scope="module")
def back_leave_response(back_leave_dates):
    start_date, end_date = back_leave_dates
    return apply_leave(
        user=settings.EMPLOYEE_USER,
        start_date=start_date,
        end_date=end_date,
        leave_reason_type=14,
        subject="Automated Back Date Leave Request",
        mail="<p>Automated back date test leave request</p>"
    )


@pytest.fixture(scope="module")
def pending_leave(leave_response, leave_dates):
    """Read approvalManager from employee's own leave, map to approver key, fetch their queue."""
    start_date, end_date = leave_dates

    my_leaves = get_my_leaves(user=settings.EMPLOYEE_USER, status="pending")
    my_leave = next(
        (l for l in my_leaves if
         l.get("start_Date", "")[:10] == start_date and
         l.get("end_Date", "")[:10] == end_date),
        None
    )
    assert my_leave is not None, \
        f"Applied leave {start_date}→{end_date} not found in employee's pending list"

    approver_name = my_leave.get("approvalManager", "")
    approver_key = settings.APPROVERS.get(approver_name)
    assert approver_key, f"Approver '{approver_name}' not found in APPROVERS map"

    pending = get_pending_leaves(approver=approver_key, from_date=start_date)
    matched = next(
        (l for l in pending if
         l.get("fromDate", "")[:10] == start_date and
         l.get("toDate", "")[:10] == end_date and
         l.get("status") == "Pending"),
        None
    )
    assert matched is not None, \
        f"Leave {start_date}→{end_date} not found in {approver_key}'s pending queue"
    return matched, approver_key


@pytest.mark.api
def test_apply_leave_response_is_dict(leave_response):
    assert isinstance(leave_response, dict), \
        f"Expected dict response, got {type(leave_response)}"


@pytest.mark.api
def test_apply_leave_has_message(leave_response):
    assert "message" in leave_response or "status" in leave_response, \
        f"No message/status in response: {leave_response}"


@pytest.mark.api
def test_apply_duplicate_leave(leave_response):
    message = leave_response.get("message", leave_response.get("status", "")).lower()
    assert "success" in message or "already exists" in message, \
        f"Unexpected response message: {message}"


@pytest.mark.api
def test_apply_leave_invalid_token():
    response = requests.post(
        f"{settings.API_BASE_URL}/Hrlense_Leave",
        headers={"Authorization": "Bearer invalid_token"},
        json={}
    )
    assert response.status_code in (401, 403), \
        f"Expected 401/403 for invalid token, got {response.status_code}"


@pytest.mark.api
def test_apply_leave_missing_payload():
    response = requests.post(
        f"{settings.API_BASE_URL}/Hrlense_Leave",
        headers=headers(settings.EMPLOYEE_USER),
        json={}
    )
    assert response.status_code in (400, 422), \
        f"Expected 400/422 for missing payload, got {response.status_code}"


@pytest.mark.api
def test_pending_leave_data_is_valid(pending_leave):
    leave, approver_key = pending_leave
    assert "id" in leave, f"Missing 'id' in leave: {leave}"
    assert leave.get("status") == "Pending", f"Expected Pending status, got: {leave.get('status')}"
    assert leave.get("fromDate"), f"Missing fromDate: {leave}"
    assert leave.get("toDate"), f"Missing toDate: {leave}"
    assert leave.get("name"), f"Missing employee name: {leave}"


@pytest.mark.api
def test_reject_leave_by_approver(pending_leave):
    leave, approver_key = pending_leave
    response = reject_leave(
        leave_id=leave["id"],
        reason="for the testing purpose only",
        approver=approver_key
    )
    message = response.get("message", "").lower()
    assert "reject" in message or "success" in message or "updated" in message, \
        f"Unexpected reject response: {response}"


@pytest.mark.api
def test_apply_back_date_leave(back_leave_response, back_leave_dates):
    start_date, _ = back_leave_dates
    message = back_leave_response.get("message", "").lower()
    assert "success" in message or "already exists" in message, \
        f"Back date leave failed: {back_leave_response}"
