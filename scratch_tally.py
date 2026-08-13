import os
import json
import requests
from dotenv import load_dotenv
from core.config import settings

# Load credentials
load_dotenv(".env.prod", override=True)
load_dotenv(".env", override=False)

PROD_API_BASE = "https://hrmsapi.jobvritta.com/api"

# Get Admin credentials
admin_user = os.getenv("ADMIN_USERNAME") or settings.USERS["admin"]["username"]
admin_pass = os.getenv("ADMIN_PASSWORD") or settings.USERS["admin"]["password"]

print(f"Logging into {PROD_API_BASE} as {admin_user}...")

login_resp = requests.post(
    f"{PROD_API_BASE}/user/login",
    data={"email": admin_user, "password": admin_pass, "user": admin_user},
    timeout=30
)

if login_resp.status_code != 200:
    # Try json payload
    login_resp = requests.post(
        f"{PROD_API_BASE}/user/login",
        json={"email": admin_user, "password": admin_pass, "user": admin_user},
        timeout=30
    )

if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    exit(1)

token = login_resp.json().get("token")
print(f"Login successful! Obtained token.")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Fetch AbsenceCase/list
print("\nFetching AbsenceCase/list (GET)...")
absence_url = f"{PROD_API_BASE}/AbsenceCase/list"
absence_params = {
    "lazyParams": json.dumps({"first": 0, "rows": 500, "page": 0, "sortField": "", "sortOrder": 1}),
    "search": "",
    "status": ""
}
abs_resp = requests.get(absence_url, headers=headers, params=absence_params, timeout=30)
print(f"AbsenceCase response status: {abs_resp.status_code}")
abs_data = abs_resp.json() if abs_resp.status_code == 200 else {}

# 2. Fetch Hrlense_Attendance/employee-attendance-summary
print("\nFetching Hrlense_Attendance/employee-attendance-summary (GET)...")
att_url = f"{PROD_API_BASE}/Hrlense_Attendance/employee-attendance-summary"
att_params = {
    "name": "",
    "from": "2026-08-01",
    "to": "2026-08-12",
    "lazyParams": json.dumps({"first": 0, "rows": 500, "page": 0, "sortField": "", "sortOrder": 1}),
    "filters": "{}"
}
att_resp = requests.get(att_url, headers=headers, params=att_params, timeout=30)
print(f"Attendance summary response status: {att_resp.status_code}")
att_data = att_resp.json() if att_resp.status_code == 200 else {}

# Save raw dumps
output_dir = "testdata/scratch"
os.makedirs(output_dir, exist_ok=True)
with open(f"{output_dir}/absence_cases_dump.json", "w") as f:
    json.dump(abs_data, f, indent=2)

with open(f"{output_dir}/attendance_summary_dump.json", "w") as f:
    json.dump(att_data, f, indent=2)

print(f"\nRaw responses dumped to {output_dir}/")

# Process and Tally
absence_records = abs_data.get("data") or abs_data if isinstance(abs_data, list) else abs_data.get("rows", [])
if isinstance(abs_data, dict) and "data" in abs_data and isinstance(abs_data["data"], dict):
    absence_records = abs_data["data"].get("rows") or abs_data["data"].get("data") or []

attendance_records = att_data.get("data") or att_data if isinstance(att_data, list) else att_data.get("rows", [])
if isinstance(att_data, dict) and "data" in att_data and isinstance(att_data["data"], dict):
    attendance_records = att_data["data"].get("rows") or att_data["data"].get("data") or []

print(f"Total Absence Case records: {len(absence_records)}")
print(f"Total Attendance Summary records: {len(attendance_records)}")

print("\n--- Absence Cases Sample ---")
if absence_records:
    print(json.dumps(absence_records[:3], indent=2))

print("\n--- Attendance Summary Sample ---")
if attendance_records:
    print(json.dumps(attendance_records[:3], indent=2))
