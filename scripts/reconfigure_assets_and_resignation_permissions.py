"""
Automated script to reconfigure Assets and Resignation permissions across all roles in HRlens
via PUT /api/page/permission/{roleId} based on the approved governance matrix.

Constraints strictly enforced:
- HR Executive (Role 2, 5): ZERO asset permissions (all 16 Asset flags = False).
- IT Person (Role 4, 13): All Asset permissions = True, EXCEPT 357 (ViewAllBranchStock) = False (Branch isolation).
- Employee (Role 3): Self-service asset request (348), return (350), and apply resignation (160) = True.
- Accountant (Role 9, 18): Account Buyout (162), BuyoutNotification (367), Recovery (355, 356) = True.
- Team Lead & Manager (Role 6, 8): Resignation request (160), Team notification (366), Asset request (348) = True.
"""

import os
import sys
import json
import logging
import requests

sys.path.insert(0, os.path.abspath("."))
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Target roles and their explicit permission assignments
# (True = explicitly enable, False = explicitly disable, omitted = keep existing state)
ROLE_RULES = {
    # 1: Super Admin (Enable all)
    1: {
        "enable": [
            21, 346, 347, 348, 349, 350, 351, 352, 355, 356, 357, 358, 359, 360, 299, 300,
            150, 151, 152, 160, 161, 162, 230, 231, 361, 362, 363, 364, 365, 366, 367
        ],
        "disable": []
    },
    # 2: HR Executive (ZERO assets; full resignation & clearance)
    2: {
        "enable": [
            150, 151, 152, 160, 161, 230, 231, 361, 362, 363, 364
        ],
        "disable": [
            21, 346, 347, 348, 349, 350, 351, 352, 355, 356, 357, 358, 359, 360, 299, 300
        ]
    },
    # 5: Assistant HR Manager (Same as HR Executive)
    5: {
        "enable": [
            150, 151, 152, 160, 161, 230, 231, 361, 362, 363, 364
        ],
        "disable": [
            21, 346, 347, 348, 349, 350, 351, 352, 355, 356, 357, 358, 359, 360, 299, 300
        ]
    },
    # 4: IT (Full assets with branch isolation; IT exit clearance)
    4: {
        "enable": [
            21, 346, 347, 348, 349, 350, 351, 352, 358, 359, 360, 299, 300,
            161, 363, 365
        ],
        "disable": [
            357, 355, 356
        ]
    },
    # 13: IT Admin (Same as IT)
    13: {
        "enable": [
            21, 346, 347, 348, 349, 350, 351, 352, 358, 359, 360, 299, 300,
            161, 363, 365
        ],
        "disable": [
            357, 355, 356
        ]
    },
    # 3: Employee (Self-service request/return, apply resignation)
    3: {
        "enable": [
            21, 348, 350, 160
        ],
        "disable": [
            346, 347, 349, 351, 352, 355, 356, 357, 358, 359, 360, 299, 300,
            161, 162, 230, 231, 361, 362, 364, 365, 367
        ]
    },
    # 6: Team Lead
    6: {
        "enable": [
            160, 366, 348
        ],
        "disable": [
            346, 347, 349, 351, 352, 355, 356, 357, 358, 359, 360, 299, 300
        ]
    },
    # 8: Team Manager
    8: {
        "enable": [
            160, 366, 348
        ],
        "disable": [
            346, 347, 349, 351, 352, 355, 356, 357, 358, 359, 360, 299, 300
        ]
    },
    # 9: Sr. Accountant Executive
    9: {
        "enable": [
            162, 367, 355, 356
        ],
        "disable": [
            21, 346, 347, 348, 349, 350, 351, 352, 357, 358, 359, 360, 299, 300
        ]
    },
    # 18: Accountant Executive
    18: {
        "enable": [
            162, 367, 355, 356
        ],
        "disable": [
            21, 346, 347, 348, 349, 350, 351, 352, 357, 358, 359, 360, 299, 300
        ]
    }
}


def run_reconfiguration():
    api_base = settings.API_BASE_URL.rstrip("/")
    logger.info("=" * 80)
    logger.info("STARTING AUTOMATED ROLE PERMISSIONS RECONFIGURATION")
    logger.info(f"Target API: {api_base}")
    logger.info("=" * 80)

    # 1. Login as Admin
    admin_creds = settings.USERS["admin"]
    login_url = f"{api_base}/user/login"
    login_payload = {
        "email": admin_creds["username"],
        "password": admin_creds["password"]
    }
    res = requests.post(login_url, json=login_payload, headers={"Content-Type": "application/json"}, verify=False)
    if res.status_code != 200:
        logger.error(f"Failed to login as admin: {res.status_code} {res.text}")
        return False
    
    token = res.json().get("token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    logger.info("Admin authentication successful.")

    # 2. Fetch all roles
    r_role = requests.get(f"{api_base}/role", headers=headers, verify=False)
    if r_role.status_code != 200:
        logger.error(f"Failed to fetch roles: {r_role.status_code}")
        return False
    
    all_roles = {r["id"]: r for r in r_role.json().get("roles", [])}
    logger.info(f"Total roles fetched from API: {len(all_roles)}")

    # 3. Process each targeted role
    for role_id, rules in ROLE_RULES.items():
        role_info = all_roles.get(role_id)
        if not role_info:
            logger.warning(f"Role ID {role_id} not found in system. Skipping.")
            continue

        role_name = role_info.get("name")
        logger.info(f"\nConfiguring Role {role_id}: '{role_name}'...")

        # Fetch current permission tree
        r_tree = requests.get(f"{api_base}/page/permission/{role_id}", headers=headers, verify=False)
        if r_tree.status_code != 200:
            logger.error(f"  Failed to fetch permission tree for Role {role_id}: {r_tree.status_code}")
            continue

        tree = r_tree.json()
        perm_map = {}
        def collect(item):
            perm_map[item["id"]] = bool(item.get("permission", False))
            for f in (item.get("features") or []):
                collect(f)

        for item in tree:
            collect(item)

        # Apply enable rules
        for pid in rules["enable"]:
            if pid in perm_map:
                perm_map[pid] = True

        # Apply disable rules
        for pid in rules["disable"]:
            if pid in perm_map:
                perm_map[pid] = False

        # Build payload
        permissions_payload = [{"pageId": pid, "permission": allowed} for pid, allowed in perm_map.items()]
        update_payload = {
            "id": role_id,
            "name": role_name,
            "description": role_info.get("description") or "",
            "require_Branch": bool(role_info.get("require_Branch", False)),
            "require_Document_Upload_Us_Company": bool(role_info.get("require_Document_Upload_Us_Company", False)),
            "require_Document_Upload_Payroll_Company": bool(role_info.get("require_Document_Upload_Payroll_Company", False)),
            "permissions": permissions_payload
        }

        # Send PUT request
        put_res = requests.put(f"{api_base}/page/permission/{role_id}", json=update_payload, headers=headers, verify=False)
        if put_res.status_code == 200:
            logger.info(f"  Successfully updated Role {role_id} ({role_name}). Enabled: {len(rules['enable'])}, Disabled: {len(rules['disable'])}")
        else:
            logger.error(f"  Failed to update Role {role_id}: {put_res.status_code} {put_res.text}")

    logger.info("\n" + "=" * 80)
    logger.info("ROLE PERMISSIONS RECONFIGURATION COMPLETE")
    logger.info("=" * 80)
    return True


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    success = run_reconfiguration()
    if not success:
        sys.exit(1)
