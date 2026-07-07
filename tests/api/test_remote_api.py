import pytest
import requests
from core.config import settings
from utils.api.base_api import headers
from utils.api.remote_api import apply_remote, get_pending_remotes


@pytest.fixture(scope="module")
def remote_dates():
    return "2026-07-04", "2026-07-04"


@pytest.fixture(scope="module")
def remote_response(remote_dates):
    start_date, end_date = remote_dates
    return apply_remote(
        user=settings.EMPLOYEE_USER,
        start_date=start_date,
        end_date=end_date,
        reason="Testing remote application",
        subject="Test Remote Application",
        mail="<p>Automated test remote request</p>"
    )


@pytest.fixture(scope="module")
def pending_remote(remote_response, remote_dates):
    start_date, end_date = remote_dates
    pending = get_pending_remotes(approver="vivek") 
    matched = next(
        (r for r in pending if
         r.get("fromDate", "")[:10] == start_date and
         r.get("toDate", "")[:10] == end_date),
        None
    )
    assert matched is not None, f"Remote not found in pending queue"
    return matched


@pytest.mark.api
def test_apply_remote_response_is_dict(remote_response):
    assert isinstance(remote_response, dict)


@pytest.mark.api
def test_apply_remote_has_message(remote_response):
    assert "message" in remote_response or "status" in remote_response


@pytest.mark.api
def test_apply_duplicate_remote(remote_response):
    message = remote_response.get("message", remote_response.get("status", "")).lower()
    assert "already exists" in message


@pytest.mark.api
def test_apply_remote_invalid_token():
    response = requests.post(
        f"{settings.API_BASE_URL}/Remote",
        headers={"Authorization": "Bearer invalid_token"},
        json={}
    )
    assert response.status_code in (401, 403)


@pytest.mark.api
def test_apply_remote_missing_payload():
    response = requests.post(
        f"{settings.API_BASE_URL}/Remote",
        headers=headers(settings.EMPLOYEE_USER),
        json={}
    )
    assert response.status_code in (400, 422)


@pytest.mark.api
def test_pending_remote_data_is_valid(pending_remote):
    assert "id" in pending_remote
    assert pending_remote.get("status") == "Pending"
    assert pending_remote.get("fromDate")
    assert pending_remote.get("toDate")
    assert pending_remote.get("name")
