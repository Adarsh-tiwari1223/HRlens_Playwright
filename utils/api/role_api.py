"""
Role and User Permission API Utilities for HRlens Portal.
Uses Playwright's built-in APIRequestContext via base_api.
"""

import json
import random
import logging
from utils.api.base_api import get, put

logger = logging.getLogger("ROLE_API")


def get_roles(user: str = "admin") -> list[dict]:
    """
    GET /role — fetch all roles in HRlens Portal.
    """
    response = get("role", user=user)
    if isinstance(response, list):
        return response
    return response.get("data", response.get("roles", []))


def get_accounts_department_users(user: str = "admin") -> list[dict]:
    """
    GET /user — fetch all users filtered by department='Accounts'.
    """
    filter_param = json.dumps({"department": {"op": "equals", "value": "Accounts", "value2": ""}})
    response = get(f"user?first=0&rows=20&filters={filter_param}", user=user)
    
    if isinstance(response, list):
        return response
    return response.get("data", response.get("users", response.get("result", [])))


def assign_random_accounts_user_role(
    role_name: str = "Accountant",
    user: str = "admin",
    require_branch: bool = True,
    require_us_company_doc: bool = True,
    require_payroll_company_doc: bool = True
) -> dict:
    """
    Dynamic 3-Step Permission & Role Management Workflow using Playwright APIRequestContext:
    1. Fetch Accounts Department users & pick a random Accounts person.
    2. Fetch roles & extract role_id for specified role_name.
    3. Update user role & configuration flags via PUT /User/updateroles/{user_id}.
    """
    # 1. Fetch Accounts Department users & pick random user
    accounts_users = get_accounts_department_users(user=user)
    if not accounts_users:
        raise ValueError("No users found in Accounts department via API.")

    selected_user = random.choice(accounts_users)
    user_id = selected_user.get("id") or selected_user.get("userId")
    user_email = selected_user.get("email") or selected_user.get("userName") or selected_user.get("name")
    logger.info(f"[STEP 1] Randomly selected Accounts person: '{user_email}' (User ID: {user_id})")

    # 2. Fetch roles & find matching role_id
    roles = get_roles(user=user)
    role_id = None
    for r in roles:
        name = r.get("name") or r.get("roleName") or r.get("title", "")
        if name.strip().lower() == role_name.strip().lower():
            role_id = r.get("id") or r.get("roleId")
            break

    if not role_id:
        role_id = 18  # Fallback default role ID for Accountant
        logger.info(f"[STEP 2] Role '{role_name}' using fallback role_id={role_id}")
    else:
        logger.info(f"[STEP 2] Resolved Role '{role_name}' → Role ID={role_id}")

    # 3. Update User Role & Flags via PUT /User/updateroles/{user_id} using Playwright API
    payload = {
        "userId": user_id,
        "roleId": role_id,
        "requireBranch": require_branch,
        "requireUsCompanyDocumentUpload": require_us_company_doc,
        "requirePayrollCompanyDocumentUpload": require_payroll_company_doc
    }

    result = put(f"User/updateroles/{user_id}", user=user, payload=payload)
    logger.info(f"[STEP 3] Successfully updated role & permissions for '{user_email}' (User ID: {user_id})")
    
    return {
        "selected_user": selected_user,
        "user_id": user_id,
        "user_email": user_email,
        "role_id": role_id,
        "role_name": role_name,
        "api_response": result
    }


def configure_account_role_company_document_permission(
    permission_to_enable: str = "ShowCompanyDocument",
    user: str = "admin"
) -> dict:
    """
    1. Selects a role starting with 'Account' (e.g. 'Accountant', 'Accounts').
    2. Enables one of the company document permissions by setting it to True:
       - ShowCompanyDocument
       - ShowPayrollCompanyDocument
       - UploadPayrollCompanyDocument
    3. Saves the role configuration via Playwright API.
    """
    logger.info("=" * 60)
    logger.info(f"STARTING ROLE CONFIGURATION WORKFLOW for Permission: '{permission_to_enable}'")
    logger.info("=" * 60)

    # 1. Fetch roles & select role starting with 'Account'
    roles = get_roles(user=user)
    matching_roles = [
        r for r in roles
        if (r.get("name") or r.get("roleName") or r.get("title", "")).strip().lower().startswith("account")
    ]

    if matching_roles:
        selected_role = random.choice(matching_roles)
        role_id = selected_role.get("id") or selected_role.get("roleId")
        role_name = selected_role.get("name") or selected_role.get("roleName") or selected_role.get("title")
        logger.info(f"[STEP 1] Selected role starting with 'Account': '{role_name}' (ID: {role_id})")
    else:
        role_id = 18
        role_name = "Accountant"
        logger.info(f"[STEP 1] No role starting with 'Account' returned from API; using fallback '{role_name}' (ID: {role_id})")

    # 2. Pick and enable target permission
    valid_permissions = ["ShowCompanyDocument", "ShowPayrollCompanyDocument", "UploadPayrollCompanyDocument"]
    if permission_to_enable not in valid_permissions:
        permission_to_enable = random.choice(valid_permissions)

    logger.info(f"[STEP 2] Enabling Company Document Permission: '{permission_to_enable}' = True")

    permission_flags = {
        "ShowCompanyDocument": permission_to_enable == "ShowCompanyDocument",
        "ShowPayrollCompanyDocument": permission_to_enable == "ShowPayrollCompanyDocument",
        "UploadPayrollCompanyDocument": permission_to_enable == "UploadPayrollCompanyDocument"
    }

    # 3. Save Role Configuration via Playwright API
    payload = {
        "roleId": role_id,
        "roleName": role_name,
        "showCompanyDocument": permission_flags["ShowCompanyDocument"],
        "showPayrollCompanyDocument": permission_flags["ShowPayrollCompanyDocument"],
        "uploadPayrollCompanyDocument": permission_flags["UploadPayrollCompanyDocument"]
    }

    logger.info(f"[STEP 3] Saving role configuration for '{role_name}' (ID: {role_id}) via Playwright API...")
    result = put(f"role/{role_id}", user=user, payload=payload)
    logger.info(f"[SUCCESS] Saved role configuration successfully for '{role_name}' (ID: {role_id})")
    logger.info("=" * 60)

    return {
        "role_id": role_id,
        "role_name": role_name,
        "permission_enabled": permission_to_enable,
        "permission_flags": permission_flags,
        "api_response": result
    }


def get_branches(user: str = "admin") -> list[dict]:
    """
    GET /Hrlense_Branch — fetch all branch locations in HRlens Portal.
    """
    try:
        response = get("Hrlense_Branch?first=0&rows=100", user=user)
        if isinstance(response, list):
            return response
        return response.get("data", response.get("branches", response.get("result", [])))
    except Exception:
        return []


def _http_get_json(endpoint: str, user: str = "admin") -> dict:
    """
    Lightweight, thread-safe HTTP GET using standard urllib (bypasses Playwright sync loop conflicts).
    """
    import urllib.request
    import urllib.parse
    from core.config import settings

    # 1. Login to get token
    try:
        login_url = f"{settings.API_BASE_URL}/user/login"
        creds = settings.USERS.get(user, settings.USERS.get("admin", {}))
        login_data = json.dumps({"email": creds["username"], "user": creds["username"], "password": creds["password"]}).encode("utf-8")
        req = urllib.request.Request(login_url, data=login_data, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            token = json.loads(resp.read().decode("utf-8")).get("token")

        # 2. Execute GET
        api_url = f"{settings.API_BASE_URL}/{endpoint}"
        get_req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(get_req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.debug(f"_http_get_json error on '{endpoint}': {e}")
        return {}


def get_user_by_email_or_username(identifier: str, user: str = "admin") -> dict:
    """
    GET /user — search and fetch single user details by email, username, or key without Playwright loop conflicts.
    """
    import re
    import urllib.parse
    from core.config import settings

    # Resolve user_key if passed
    if identifier in settings.USERS:
        target_email = settings.USERS[identifier].get("username", identifier)
    else:
        target_email = identifier

    # Extract first name / tokens from email (e.g. 'tejasav.jaiswal' -> ['Tejasav', 'Jaiswal'])
    prefix = target_email.split("@")[0]
    name_tokens = [t.capitalize() for t in re.split(r"[._-]", prefix) if len(t) > 2]
    if not name_tokens:
        name_tokens = [prefix]

    for token in name_tokens:
        filter_param = urllib.parse.quote(json.dumps({"name": {"op": "contains", "value": token, "value2": ""}}))
        response = _http_get_json(f"user?first=0&rows=50&filters={filter_param}", user=user)

        users_list = []
        if isinstance(response, list):
            users_list = response
        elif isinstance(response, dict):
            users_list = response.get("users", response.get("data", response.get("result", [])))

        for u in users_list:
            u_email = (u.get("email") or "").strip().lower()
            if u_email == target_email.strip().lower() or target_email.strip().lower() in u_email or prefix.lower() in u_email:
                u["id"] = u.get("login_ID") or u.get("id") or u.get("userId")
                u["userId"] = u["id"]
                return u

    return {}


def map_env_employee_role_and_permissions(
    user_key: str,
    role_name: str = "IT",
    branch_name: str = None,
    admin_user: str = "admin",
    require_branch: bool = True
) -> dict:
    """
    Dynamically maps any employee in .env (or settings.USERS) to a target Role, Branch, and Permissions via API.
    1. Reads employee identifier from settings.USERS.
    2. Resolves userId via GET /api/user.
    3. Resolves roleId via GET /api/role for role_name.
    4. Resolves branchId via GET /api/branch if branch_name is specified.
    5. Updates user role & branch scoping via PUT /api/User/updateroles/{userId}.
    """
    from core.config import settings

    user_info = settings.USERS.get(user_key, {})
    email = user_info.get("username") or user_key

    logger.info("=" * 60)
    logger.info(f"[DYNAMIC API MAPPING] Mapping '{user_key}' ({email}) -> Role: '{role_name}', Branch: '{branch_name or 'Unchanged'}'")
    logger.info("=" * 60)

    # 1. Fetch User ID
    user_data = get_user_by_email_or_username(email, user=admin_user)
    user_id = user_data.get("id") or user_data.get("login_ID") or user_data.get("userId")
    if not user_id:
        raise ValueError(f"Could not find user '{email}' via /api/user")

    # 2. Fetch Role ID
    roles = get_roles(user=admin_user)
    role_id = None
    for r in roles:
        name = r.get("name") or r.get("roleName") or r.get("title", "")
        if name.strip().lower() == role_name.strip().lower() or role_name.strip().lower() in name.strip().lower():
            role_id = r.get("id") or r.get("roleId")
            role_name = name
            break
    if not role_id:
        role_id = 4  # Fallback default IT role ID

    # 3. Fetch Branch ID if branch_name specified
    branch_id = user_data.get("branchID") or user_data.get("branch_ID")
    if branch_name:
        branches = get_branches(user=admin_user)
        for b in branches:
            b_name = b.get("name") or b.get("branchName") or b.get("branch_Name") or ""
            if branch_name.strip().lower() in b_name.strip().lower():
                branch_id = b.get("id") or b.get("branchId") or b.get("branch_ID")
                break

    # 4. Apply Update via PUT /api/User/updateroles/{userId}
    payload = {
        "userId": user_id,
        "roleId": role_id,
        "branchId": branch_id,
        "requireBranch": require_branch,
        "requireUsCompanyDocumentUpload": False,
        "requirePayrollCompanyDocumentUpload": False
    }

    result = put(f"User/updateroles/{user_id}", user=admin_user, payload=payload)
    logger.info(f"[SUCCESS] Mapped '{email}' (User ID: {user_id}) -> Role: '{role_name}' (ID: {role_id}), Branch ID: {branch_id}")

    return {
        "user_key": user_key,
        "email": email,
        "user_id": user_id,
        "role_id": role_id,
        "role_name": role_name,
        "branch_id": branch_id,
        "branch_name": branch_name or user_data.get("branch"),
        "api_response": result
    }


def get_user_permissions(user_key_or_email: str, admin_user: str = "admin") -> dict:
    """
    Fetches the active mapped role, branch, and permission set for an employee via API.
    """
    user_data = get_user_by_email_or_username(user_key_or_email, user=admin_user)
    if not user_data:
        return {"error": "User not found", "permissions": []}

    user_id = user_data.get("id") or user_data.get("login_ID") or user_data.get("userId")
    assigned_roles = user_data.get("roles", [])
    branch_name = user_data.get("branch") or user_data.get("branchName")
    assigned_branches = [b.get("branch_Name") or b.get("name") for b in user_data.get("assignedBranches", []) if b.get("branch_Name") or b.get("name")]

    return {
        "user_id": user_id,
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "role_name": ", ".join([r.get("name") for r in assigned_roles]) if assigned_roles else "Employee",
        "roles": assigned_roles,
        "branch_name": branch_name,
        "assigned_branches": assigned_branches,
        "permissions": [f"Role: {r.get('name')}" for r in assigned_roles] + ([f"Branch Access: {b}" for b in assigned_branches] if assigned_branches else [f"Primary Branch: {branch_name}"])
    }
