import sys
import os
sys.path.insert(0, os.path.abspath("."))
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Official Asset Module Branch Mapping
BRANCH_MAP = {
    "varanasi": 1,
    "agra": 2,
    "meerut": 3,
    "lucknow": 4,
    "ranchi": 5,
    "bhubaneswar": 6,
    "jaipur": 7,
    "greater noida": 10,
    "noida nx-one": 9,
    "noida": 8,
    "gurgaon": 9  # Map Gurgaon to Noida NX-One so it has a valid branch
}

def resolve_target_branch_id(asset: dict) -> int:
    notes = (asset.get("notes") or "").lower()
    name = (asset.get("asset_Name") or "").lower()
    serial = (asset.get("serial_No") or "").lower()
    combined = f"{notes} {name} {serial}"

    if "greater noida" in combined:
        return 10
    if "noida nx-one" in combined or "nx-one" in combined:
        return 9
    for branch_name, branch_id in BRANCH_MAP.items():
        if branch_name in combined:
            return branch_id
    return 1  # Default fallback to Varanasi

def update_single_asset(asset: dict, target_branch_id: int, headers: dict) -> tuple[int, bool, str]:
    aid = asset["id"]
    payload = dict(asset)
    payload["branch_Id"] = target_branch_id
    try:
        resp = requests.put(f"{settings.API_BASE_URL}/Asset/assets/{aid}", headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 204):
            return aid, True, f"Updated to branch_Id {target_branch_id}"
        else:
            return aid, False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as ex:
        return aid, False, str(ex)

def fix_all_unknown_assets():
    logger.info("Logging in to authenticate...")
    creds = settings.USERS["admin"]
    resp = requests.post(
        f"{settings.API_BASE_URL}/user/login",
        json={"email": creds["username"], "user": creds["username"], "password": creds["password"]},
        timeout=15
    )
    token = resp.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    logger.info("Checking initial dashboard status...")
    r_dash = requests.get(f"{settings.API_BASE_URL}/Asset/dashboard", headers=headers, timeout=15)
    if r_dash.status_code == 200:
        logger.info(f"Initial by_Location: {r_dash.json().get('by_Location')}")

    logger.info("Fetching all assets from database...")
    r_assets = requests.get(f"{settings.API_BASE_URL}/Asset/assets?page=1&rows=1000", headers=headers, timeout=20)
    all_assets = r_assets.json().get("data", [])
    logger.info(f"Total assets fetched: {len(all_assets)}")

    # Target assets that are in 'Unknown' or have branch_Id not in 1..10
    unknown_assets = [a for a in all_assets if a.get("branch_Id") not in range(1, 11) or not a.get("branch_Name")]
    logger.info(f"Found {len(unknown_assets)} assets needing branch assignment.")

    if not unknown_assets:
        logger.info("No assets to update! All assets already have valid branches.")
        return

    success_count = 0
    fail_count = 0

    logger.info(f"Updating {len(unknown_assets)} assets in parallel via PUT /Asset/assets/{{id}}...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(update_single_asset, asset, resolve_target_branch_id(asset), headers): asset
            for asset in unknown_assets
        }
        for future in as_completed(futures):
            aid, ok, msg = future.result()
            if ok:
                success_count += 1
            else:
                fail_count += 1
                logger.warning(f"Failed to update asset {aid}: {msg}")

    logger.info(f"\n==========================================")
    logger.info(f"PUT Updates Complete! Success: {success_count}, Failed: {fail_count}")
    logger.info(f"==========================================")

    logger.info("Verifying final dashboard status...")
    r_dash_final = requests.get(f"{settings.API_BASE_URL}/Asset/dashboard", headers=headers, timeout=15)
    if r_dash_final.status_code == 200:
        by_loc = r_dash_final.json().get("by_Location", [])
        logger.info("Updated Dashboard by_Location:")
        for loc in by_loc:
            logger.info(f"  Branch {loc.get('branch_Id')} ({loc.get('location_Name')}): Total={loc.get('total')}, Available={loc.get('available')}")

if __name__ == "__main__":
    fix_all_unknown_assets()
