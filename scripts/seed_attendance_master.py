"""
Seed Attendance Master Data for All Companies, Branches, and Departments.
Creates distinct individual records for each valid (Company, Branch, Department) combination
using the defined default attendance settings.
"""

import os
import json
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from testdata.static.attendance_settings import DEFAULT_ATTENDANCE_SETTING

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_BASE_URL = "https://audit.jobvritta.com/api"


def get_admin_token() -> str:
    """Extracts active Admin Bearer JWT token from .auth/admin.json."""
    auth_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".auth", "admin.json")
    if not os.path.exists(auth_file):
        raise FileNotFoundError(f"Auth file not found at: {auth_file}")

    with open(auth_file, "r", encoding="utf-8") as f:
        auth_data = json.load(f)

    session_storage = auth_data.get("sessionStorage", {})
    login_data_str = session_storage.get("loginData", "{}")
    login_data = json.loads(login_data_str) if isinstance(login_data_str, str) else login_data_str
    token = login_data.get("token", "")
    if not token:
        raise ValueError("Could not extract token from .auth/admin.json")
    return token


def get_filter_options(headers: dict) -> tuple[list[dict], list[dict]]:
    """Fetches all valid Branches and Departments from AttendanceFilter API."""
    url = f"{API_BASE_URL}/Filters/AttendanceFilter"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("filterOptions", {})
    branches = data.get("Branch", [])
    departments = data.get("Department", [])
    return branches, departments


def get_existing_attendance_settings(headers: dict) -> set[tuple[int, int, int]]:
    """Fetches existing records to avoid duplicate creation."""
    url = f"{API_BASE_URL}/AttandanceMaster?lazyParams=%7B%22first%22:0,%22rows%22:5000%7D"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    existing = set()
    for item in data:
        cid = item.get("companyId") or item.get("company_Id")
        bid = item.get("branchId") or item.get("branch_Id")
        did = item.get("departmentId") or item.get("department_Id")
        if cid and bid and did:
            existing.add((int(cid), int(bid), int(did)))
    return existing


def post_attendance_setting(session: requests.Session, headers: dict, payload: dict) -> tuple[bool, str]:
    """Posts a single Attendance Master setting."""
    url = f"{API_BASE_URL}/AttandanceMaster"
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            res_data = resp.json()
            return True, f"ID {res_data.get('id')}"
        return False, f"Status {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, str(e)


def main():
    logger.info("==================================================")
    logger.info("SEED ATTENDANCE MASTER — ALL COMPANIES, BRANCHES, DEPARTMENTS")
    logger.info("==================================================")

    token = get_admin_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logger.info("Fetching filter options (Branches & Departments)...")
    branches, departments = get_filter_options(headers)
    logger.info(f"Retrieved {len(branches)} branches and {len(departments)} departments.")

    logger.info("Fetching existing attendance master records...")
    existing = get_existing_attendance_settings(headers)
    logger.info(f"Found {len(existing)} existing records in Attendance Master.")

    # Build work queue
    tasks = []
    skipped = 0

    for branch in branches:
        comp_id = branch.get("parentId")
        branch_id = branch.get("id")
        branch_name = branch.get("name", "")

        if not comp_id or not branch_id:
            continue

        for dept in departments:
            dept_id = dept.get("id")
            dept_name = dept.get("name", "")

            if not dept_id:
                continue

            triplet = (int(comp_id), int(branch_id), int(dept_id))
            if triplet in existing:
                skipped += 1
                continue

            payload = {
                "companyId": int(comp_id),
                "companyIds": [int(comp_id)],
                "branchId": int(branch_id),
                "branchIds": [int(branch_id)],
                "departmentId": int(dept_id),
                "departmentIds": [int(dept_id)],
                "totalWorkingHour": DEFAULT_ATTENDANCE_SETTING["totalWorkingHour"],
                "halfDayTime": DEFAULT_ATTENDANCE_SETTING["halfDayTime"],
                "lateMinute": DEFAULT_ATTENDANCE_SETTING["lateMinute"],
                "graceHour": DEFAULT_ATTENDANCE_SETTING["graceHour"],
                "shortLeaveFrom": DEFAULT_ATTENDANCE_SETTING["shortLeaveFrom"],
                "shortLeaveTo": DEFAULT_ATTENDANCE_SETTING["shortLeaveTo"],
                "shortLeaveCountForHalfDay": DEFAULT_ATTENDANCE_SETTING["shortLeaveCountForHalfDay"],
            }
            tasks.append((comp_id, branch_name, dept_name, payload))

    total_to_create = len(tasks)
    logger.info(f"Total targets: {len(branches) * len(departments)} | Already existing: {skipped} | To create: {total_to_create}")

    if total_to_create == 0:
        logger.info("All company-branch-department combinations are already created. Exiting.")
        return

    logger.info(f"Starting creation of {total_to_create} records using 8 concurrent workers...")

    created_count = 0
    error_count = 0

    session = requests.Session()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(post_attendance_setting, session, headers, payload): (cid, bname, dname)
            for cid, bname, dname, payload in tasks
        }

        for i, future in enumerate(as_completed(futures), 1):
            cid, bname, dname = futures[future]
            success, msg = future.result()
            if success:
                created_count += 1
            else:
                error_count += 1
                logger.warning(f"Failed ({cid}, '{bname}', '{dname}'): {msg}")

            if i % 100 == 0 or i == total_to_create:
                logger.info(f"Progress: {i}/{total_to_create} completed (Created: {created_count}, Errors: {error_count})")

    logger.info("==================================================")
    logger.info("SEED EXECUTION SUMMARY")
    logger.info("==================================================")
    logger.info(f"Total Target Combinations : {len(branches) * len(departments)}")
    logger.info(f"Pre-existing Records      : {skipped}")
    logger.info(f"Newly Created Records     : {created_count}")
    logger.info(f"Failed Records            : {error_count}")
    logger.info("==================================================")

    # Verification query
    final_resp = requests.get(f"{API_BASE_URL}/AttandanceMaster?lazyParams=%7B%22first%22:0,%22rows%22:10%7D", headers=headers)
    if final_resp.status_code == 200:
        total_in_db = final_resp.json().get("totalRecords", "N/A")
        logger.info(f"VERIFIED TOTAL RECORDS IN ATTENDANCE MASTER: {total_in_db}")


if __name__ == "__main__":
    main()
