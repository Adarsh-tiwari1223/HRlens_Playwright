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
