"""
Seed Asset Master Data via REST API.

Populates Categories, Subcategories, and Vendors into HRlens database:
- Step 1: Categories (Hardware, Peripherals, Networking, Office Furniture)
- Step 2: Sub-Categories mapped to Category IDs with Code Prefixes (LAP, DSK, MON, MOU, KEY, HDP, RTR)
- Step 3: Vendors (Dell India, HP Enterprise, Logitech Systems) with GST & AMC
- Step 4: Verification via GET queries
"""

import sys
import logging
import requests
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_asset_masters")


def get_token(user: str = "admin") -> str:
    creds = settings.USERS[user]
    url = f"{settings.API_BASE_URL}/user/login"
    payload = {
        "email": creds["username"],
        "user": creds["username"],
        "password": creds["password"]
    }
    resp = requests.post(url, json=payload, timeout=15)
    if resp.status_code == 200:
        token = resp.json().get("token", "")
        logger.info("Admin authentication successful via API.")
        return token
    else:
        logger.error(f"Failed to authenticate: {resp.status_code} - {resp.text}")
        sys.exit(1)


def main():
    token = get_token("admin")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # ══════════════════════════════════════════════════════════════════
    # STEP 1: CATEGORIES
    # ══════════════════════════════════════════════════════════════════
    logger.info("=== STEP 1: SEEDING ASSET CATEGORIES ===")
    cat_url = f"{settings.API_BASE_URL}/AssesstsMaster/categories"

    # Query existing
    existing_cats = {}
    try:
        resp = requests.get(cat_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cat_list = data if isinstance(data, list) else data.get("data", [])
            for c in cat_list:
                name = c.get("category_Name") or c.get("name") or c.get("categoryName")
                c_id = c.get("id") or c.get("category_Id")
                if name:
                    existing_cats[name.strip().lower()] = c_id
            logger.info(f"Existing Categories: {list(existing_cats.keys())}")
    except Exception as e:
        logger.warning(f"Error checking existing categories: {e}")

    from testdata.static.asset_categories import ASSET_CATEGORIES_DATASET

    categories_to_seed = [{"name": cat["name"], "desc": f"{cat['name']} Enterprise Assets"} for cat in ASSET_CATEGORIES_DATASET]
    category_map = {}  # name -> id

    for cat in categories_to_seed:
        c_name = cat["name"]
        if c_name.lower() in existing_cats:
            cat_id = existing_cats[c_name.lower()]
            category_map[c_name] = cat_id
            logger.info(f"Category '{c_name}' already exists (ID: {cat_id}). Skipped.")
        else:
            payload = {"category_Name": c_name, "description": cat["desc"]}
            resp = requests.post(cat_url, headers=headers, json=payload, timeout=15)
            if resp.status_code in (200, 201):
                res_json = resp.json()
                cat_id = None
                if isinstance(res_json, dict):
                    cat_id = res_json.get("id") or res_json.get("category_Id") or res_json.get("data", {}).get("id")
                logger.info(f"Created Category: '{c_name}' -> Status: {resp.status_code} | ID: {cat_id}")
                if cat_id:
                    category_map[c_name] = cat_id
            else:
                logger.error(f"Failed to create category '{c_name}': {resp.status_code} - {resp.text}")

    # Refresh categories to ensure we have all IDs
    resp = requests.get(cat_url, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        cat_list = data if isinstance(data, list) else data.get("data", [])
        for c in cat_list:
            name = c.get("category_Name") or c.get("name") or c.get("categoryName")
            c_id = c.get("id") or c.get("category_Id")
            for cat_data in ASSET_CATEGORIES_DATASET:
                if name and cat_data["name"].lower() == name.strip().lower():
                    category_map[cat_data["name"]] = c_id

    logger.info(f"Resolved Category IDs: {category_map}")

    # ══════════════════════════════════════════════════════════════════
    # STEP 2: SUB-CATEGORIES
    # ══════════════════════════════════════════════════════════════════
    logger.info("=== STEP 2: SEEDING ASSET SUB-CATEGORIES ===")
    subcat_url = f"{settings.API_BASE_URL}/AssesstsMaster/subCategory"

    # Query existing subcategories
    existing_subcats = set()
    try:
        resp = requests.get(subcat_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            subcat_list = data if isinstance(data, list) else data.get("data", [])
            for sc in subcat_list:
                s_name = sc.get("subCategory_Name") or sc.get("name") or sc.get("subCategoryName")
                if s_name:
                    existing_subcats.add(s_name.strip().lower())
            logger.info(f"Existing Sub-Categories: {list(existing_subcats)}")
    except Exception as e:
        logger.warning(f"Error checking existing subcategories: {e}")

    subcategories_to_seed = []
    for cat_data in ASSET_CATEGORIES_DATASET:
        for sub in cat_data.get("subcategories", []):
            subcategories_to_seed.append({
                "cat": cat_data["name"],
                "name": sub["name"],
                "prefix": sub.get("code_prefix", sub["name"][:3].upper()),
                "desc": f"{sub['name']} Sub-Category"
            })

    for sc in subcategories_to_seed:
        sc_name = sc["name"]
        cat_name = sc["cat"]
        cat_id = category_map.get(cat_name)

        if not cat_id:
            logger.warning(f"Skipping subcategory '{sc_name}': Parent category '{cat_name}' ID not found.")
            continue

        if sc_name.lower() in existing_subcats:
            logger.info(f"Sub-Category '{sc_name}' already exists. Skipped.")
            continue

        payload = {
            "Category_Id": cat_id,
            "SubCategory_Name": sc_name,
            "Code_Prefix": sc["prefix"],
            "Description": sc["desc"]
        }
        resp = requests.post(subcat_url, headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            logger.info(f"Created Sub-Category: '{sc_name}' (Prefix: {sc['prefix']}, Cat: {cat_name}) -> Status: {resp.status_code}")
        else:
            logger.error(f"Failed to create subcategory '{sc_name}': {resp.status_code} - {resp.text}")

    # ══════════════════════════════════════════════════════════════════
    # STEP 3: VENDORS
    # ══════════════════════════════════════════════════════════════════
    logger.info("=== STEP 3: SEEDING ASSET VENDORS ===")
    vendor_url = f"{settings.API_BASE_URL}/AssesstsMaster/vendors"

    # Query existing vendors
    existing_vendors = set()
    try:
        resp = requests.get(vendor_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            vendor_list = data if isinstance(data, list) else data.get("data", [])
            for v in vendor_list:
                v_name = v.get("vendor_Name") or v.get("name") or v.get("vendorName")
                if v_name:
                    existing_vendors.add(v_name.strip().lower())
            logger.info(f"Existing Vendors: {list(existing_vendors)}")
    except Exception as e:
        logger.warning(f"Error checking existing vendors: {e}")

    vendors_to_seed = [
        {
            "name": "Dell India Technologies",
            "contact": "Rajesh Kumar",
            "phone": "9876543210",
            "email": "procurement@dell-india.com",
            "address": "DLF CyberCity, Building 10, Gurugram, Haryana",
            "gst": "06AABCD1234E1Z5",
            "amc": True
        },
        {
            "name": "HP Enterprise Solutions",
            "contact": "Amitabh Sharma",
            "phone": "9812345678",
            "email": "support@hp-enterprises.com",
            "address": "Embassy Golf Links, Bengaluru, Karnataka",
            "gst": "29AABCH5678F1Z2",
            "amc": True
        },
        {
            "name": "Logitech India Solutions",
            "contact": "Pooja Verma",
            "phone": "9988776655",
            "email": "orders@logitech-india.com",
            "address": "Bandra Kurla Complex, Mumbai, Maharashtra",
            "gst": "27AABCL9012G1Z9",
            "amc": False
        }
    ]

    for v in vendors_to_seed:
        v_name = v["name"]
        if v_name.lower() in existing_vendors:
            logger.info(f"Vendor '{v_name}' already exists. Skipped.")
            continue

        payload = {
            "Vendor_Name": v_name,
            "Contact_Person": v["contact"],
            "Phone": v["phone"],
            "Email": v["email"],
            "Address": v["address"],
            "GST": v["gst"],
            "Supports_Amc": v["amc"]
        }
        resp = requests.post(vendor_url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 404:
            resp = requests.post(f"{settings.API_BASE_URL}/AssesstsMaster/vendor", headers=headers, json=payload, timeout=15)

        if resp.status_code in (200, 201):
            logger.info(f"Created Vendor: '{v_name}' (GST: {v['gst']}) -> Status: {resp.status_code}")
        else:
            logger.error(f"Failed to create vendor '{v_name}': {resp.status_code} - {resp.text}")

    # ══════════════════════════════════════════════════════════════════
    # STEP 4: FINAL AUDIT VERIFICATION
    # ══════════════════════════════════════════════════════════════════
    logger.info("=== STEP 4: VERIFYING SEEDED MASTER DATA ===")
    cat_resp = requests.get(cat_url, headers=headers, timeout=15).json()
    subcat_resp = requests.get(subcat_url, headers=headers, timeout=15).json()
    vendor_resp = requests.get(vendor_url, headers=headers, timeout=15).json()

    cats_final = cat_resp if isinstance(cat_resp, list) else cat_resp.get("data", [])
    subcats_final = subcat_resp if isinstance(subcat_resp, list) else subcat_resp.get("data", [])
    vendors_final = vendor_resp if isinstance(vendor_resp, list) else vendor_resp.get("data", [])

    print("\n" + "=" * 70)
    print("ASSET MASTER SEEDING REPORT")
    print("=" * 70)
    print(f"Total Categories in DB     : {len(cats_final)}")
    for c in cats_final:
        print(f"   • ID: {c.get('id')} | Name: {c.get('category_Name') or c.get('name')}")
    print(f"\nTotal Sub-Categories in DB : {len(subcats_final)}")
    for sc in subcats_final:
        print(f"   • ID: {sc.get('id')} | Name: {sc.get('subCategory_Name') or sc.get('name')} | Prefix: {sc.get('code_Prefix')} | Cat ID: {sc.get('category_Id')}")
    print(f"\nTotal Vendors in DB        : {len(vendors_final)}")
    for v in vendors_final:
        print(f"   • ID: {v.get('id')} | Name: {v.get('vendor_Name') or v.get('name')} | GST: {v.get('gst')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
