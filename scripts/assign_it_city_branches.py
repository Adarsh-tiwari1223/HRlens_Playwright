"""
Script to bulk-assign City Branch IDs to IT Users via PUT /api/User/updateroles/{userId}.

For each IT user:
- Identifies their home branch / city (e.g. Varanasi, Noida, Agra, Greater Noida, Meerut, etc.)
- Maps all branch IDs for that city from GET /Hrlense_Branch
- Calls PUT /api/User/updateroles/{userId} with:
  {
    "RoleIds": [3, 4],
    "AssignedBranchIds": [all_branch_ids_for_that_city],
    "PayrollCompanyIds": [],
    "UsCompanyIds": []
  }
"""

import os
import sys
import re
import json
import logging

sys.path.insert(0, os.path.abspath("."))

from core.config import settings
from utils.api.base_api import get, put, post
from pages.base_page import format_ascii_table
from utils.api.role_api import get_user_by_email_or_username
from utils.branch_it_selector import BRANCH_RESPONSIBILITY_MAP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_assign_it_city_branches():
    logger.info("=" * 80)
    logger.info("STARTING BULK IT USER CITY BRANCH ASSIGNMENT")
    logger.info(f"Target Environment : {settings.ENV} | API: {settings.API_BASE_URL}")
    logger.info("=" * 80)

    # 1. Fetch All Branches from API
    logger.info("Step 1: Fetching all company branches via GET /Hrlense_Branch...")
    from utils.api.payroll_api import get_branches
    all_branches = get_branches()
    logger.info(f"Total branches fetched: {len(all_branches)}")

    # Group branch IDs by City
    city_branch_ids = {}
    for b in all_branches:
        b_id = b.get("id")
        b_name = b.get("branch_Name", "").strip()
        if not b_id or not b_name:
            continue

        m = re.search(r"\((.*?)\)", b_name)
        city = m.group(1).strip().title() if m else b_name.strip().title()

        if city not in city_branch_ids:
            city_branch_ids[city] = []
        if b_id not in city_branch_ids[city]:
            city_branch_ids[city].append(b_id)

    logger.info("\n" + "=" * 60)
    logger.info("DISCOVERED CITY -> BRANCH ID MAPPINGS:")
    logger.info("=" * 60)
    for city, ids in sorted(city_branch_ids.items()):
        logger.info(f"• {city:<16} : {len(ids)} branch IDs -> {ids}")
    logger.info("=" * 60 + "\n")

    # 2. Collect All IT Person Targets
    it_targets = []
    for city, data in BRANCH_RESPONSIBILITY_MAP.items():
        for person in data.get("it_persons", []):
            it_targets.append({
                "name": person["name"],
                "email": person["email"],
                "city": city,
                "user_key": person["user_key"]
            })

    results = []

    # 3. For each IT target, resolve userId and send PUT /api/User/updateroles/{userId}
    for target in it_targets:
        name = target["name"]
        email = target["email"]
        city = target["city"]

        # Resolve user details
        user_data = get_user_by_email_or_username(email)
        u_id = user_data.get("id") or user_data.get("login_ID") or user_data.get("userId")

        if not u_id:
            logger.warning(f"[SKIP] Could not resolve User ID for '{name}' ({email})")
            results.append({
                "user_id": "N/A",
                "name": name,
                "email": email,
                "city": city,
                "assigned_branches": "N/A",
                "status": "USER NOT FOUND"
            })
            continue

        is_it_admin = email.lower() in ["shubham@technovion.com", "ashu.sain@corehuntinc.com"] or "admin" in target.get("user_key", "")
        role_ids = [3, 13] if is_it_admin else [3, 4]
        assigned_branches = [] if is_it_admin else target_branch_ids

        # Prepare exact payload ensuring Employee Role (ID 3) is always included
        payload = {
            "RoleIds": role_ids,
            "AssignedBranchIds": assigned_branches,
            "PayrollCompanyIds": [],
            "UsCompanyIds": []
        }

        endpoint = f"User/updateroles/{u_id}"
        status_msg = "SUCCESS (HTTP 200)"

        try:
            res = put(endpoint, user="admin", payload=payload)
            logger.info(f"[SUCCESS] PUT {endpoint} -> {name} ({email}) | City: {city} | Branch IDs: {target_branch_ids}")
        except Exception as ex:
            try:
                res = post(endpoint, user="admin", payload=payload)
                logger.info(f"[POST FALLBACK SUCCESS] POST {endpoint} -> {name} ({email}) | City: {city} | Branch IDs: {target_branch_ids}")
            except Exception as e2:
                status_msg = f"FAILED: {e2}"
                logger.error(f"[ERROR] Failed {endpoint} for {name} ({email}): {e2}")

        results.append({
            "user_id": u_id,
            "name": name,
            "email": email,
            "city": city,
            "assigned_branches": f"{len(target_branch_ids)} IDs: {target_branch_ids}",
            "status": status_msg
        })

    # 4. Print Structured ASCII Summary Report
    print("\n" + format_ascii_table("IT USER CITY BRANCH ASSIGNMENT RESULTS (PUT API)", results))
    logger.info("Bulk IT User City Branch Assignment Completed.")


if __name__ == "__main__":
    run_assign_it_city_branches()
