import pytest
import requests
from datetime import date, timedelta
from core.config import settings
from utils.api.base_api import get_token


BASE_URL = settings.API_BASE_URL


@pytest.fixture(scope="module")
def auth_headers():
    return {"Authorization": f"Bearer {get_token(settings.EMPLOYEE_USER)}"}


@pytest.fixture(scope="module")
def leave_payload():
    start_date = (date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET)).strftime("%Y-%m-%d")
    end_date = (date.today() + timedelta(days=settings.LEAVE_FROM_OFFSET + settings.LEAVE_TO_OFFSET)).strftime("%Y-%m-%d")
    return {
        "startSession": "Full Day",
        "endSession": "Full Day",
        "start_Date": start_date,
        "end_Date": end_date,
        "leave_Reason_Type": 14,
        "mail": "<p>Automated test leave request</p>",
        "subject": "Automated Leave Request",
        "work_Delegation_Id": 0
    }


@pytest.mark.api
def test_apply_leave_status_code(auth_headers, leave_payload):
    response = requests.post(
        f"{BASE_URL}/Hrlense_Leave",
        headers=auth_headers,
        json=leave_payload
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Body: {response.text}"


@pytest.mark.api
def test_apply_leave_response_structure(auth_headers, leave_payload):
    response = requests.post(
        f"{BASE_URL}/Hrlense_Leave",
        headers=auth_headers,
        json=leave_payload
    )
    data = response.json()
    assert isinstance(data, dict), f"Expected dict response, got {type(data)}"
    assert "message" in data or "status" in data, f"No message/status in response: {data}"


@pytest.mark.api
def test_apply_leave_success_message(auth_headers, leave_payload):
    response = requests.post(
        f"{BASE_URL}/Hrlense_Leave",
        headers=auth_headers,
        json=leave_payload
    )
    data = response.json()
    message = data.get("message", data.get("status", "")).lower()
    assert "success" in message or "already exists" in message, \
        f"Unexpected response message: {message}"


@pytest.mark.api
def test_apply_leave_invalid_token():
    response = requests.post(
        f"{BASE_URL}/Hrlense_Leave",
        headers={"Authorization": "Bearer invalid_token"},
        json={}
    )
    assert response.status_code in (401, 403), \
        f"Expected 401/403 for invalid token, got {response.status_code}"
