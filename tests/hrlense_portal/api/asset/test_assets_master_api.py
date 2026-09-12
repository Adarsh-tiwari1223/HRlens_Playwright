"""
Asset Master API Test Suite (HRlens Portal).

Validates all REST endpoints and HTTP methods (GET, POST, PUT) on Asset Master:
1. Category     (/api/AssesstsMaster/categories)
2. Sub-Category (/api/AssesstsMaster/subCategory)
3. Vendor       (/api/AssesstsMaster/vendors)

All read queries (GET) are imported from the shared query utility:
    utils.api.asset_api

Execution:
    docker compose -f docker/compose.yaml run --rm tests pytest tests/hrlense_portal/api/Assets/test_assets_master_api.py -v -s
"""

import time
import logging
import requests
import pytest
from core.config import settings
from utils.api.asset.asset_api import (
    get_auth_headers,
    get_categories,
    get_subcategories,
    get_vendors,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ============================================================================
# LOCAL TEST MUTATION HELPERS (POST / PUT)
# ============================================================================

def post_category(category_name: str, description: str = "", user: str = "admin") -> requests.Response:
    url = f"{settings.API_BASE_URL}/AssesstsMaster/categories"
    payload = {"category_Name": category_name, "description": description}
    return requests.post(url, headers=get_auth_headers(user), json=payload, timeout=15)


def put_category(category_id: int, category_name: str, description: str = "", user: str = "admin") -> requests.Response:
    url = f"{settings.API_BASE_URL}/AssesstsMaster/categories"
    payload = {"id": category_id, "category_Name": category_name, "description": description}
    resp = requests.put(url, headers=get_auth_headers(user), json=payload, timeout=15)
    if resp.status_code in (404, 405):
        resp = requests.put(f"{url}/{category_id}", headers=get_auth_headers(user), json=payload, timeout=15)
    return resp


def post_subcategory(category_id: int, subcategory_name: str, code_prefix: str = "", description: str = "", user: str = "admin") -> requests.Response:
    url = f"{settings.API_BASE_URL}/AssesstsMaster/subCategory"
    payload = {
        "Category_Id": category_id,
        "SubCategory_Name": subcategory_name,
        "Code_Prefix": code_prefix,
        "Description": description
    }
    return requests.post(url, headers=get_auth_headers(user), json=payload, timeout=15)


def put_subcategory(subcategory_id: int, category_id: int, subcategory_name: str, code_prefix: str = "", description: str = "", user: str = "admin") -> requests.Response:
    url = f"{settings.API_BASE_URL}/AssesstsMaster/subCategory"
    payload = {
        "id": subcategory_id,
        "Category_Id": category_id,
        "SubCategory_Name": subcategory_name,
        "Code_Prefix": code_prefix,
        "Description": description
    }
    resp = requests.put(url, headers=get_auth_headers(user), json=payload, timeout=15)
    if resp.status_code in (404, 405):
        resp = requests.put(f"{url}/{subcategory_id}", headers=get_auth_headers(user), json=payload, timeout=15)
    return resp


def post_vendor(vendor_name: str, contact_person: str = "", phone: str = "", email: str = "", address: str = "", gst: str = "", supports_amc: bool = True, user: str = "admin") -> requests.Response:
    url = f"{settings.API_BASE_URL}/AssesstsMaster/vendors"
    payload = {
        "Vendor_Name": vendor_name,
        "Contact_Person": contact_person,
        "Phone": phone,
        "Email": email,
        "Address": address,
        "GST": gst,
        "Supports_Amc": supports_amc
    }
    resp = requests.post(url, headers=get_auth_headers(user), json=payload, timeout=15)
    if resp.status_code == 404:
        resp = requests.post(f"{settings.API_BASE_URL}/AssesstsMaster/vendor", headers=get_auth_headers(user), json=payload, timeout=15)
    return resp


def put_vendor(vendor_id: int, vendor_name: str, contact_person: str = "", phone: str = "", email: str = "", address: str = "", gst: str = "", supports_amc: bool = True, user: str = "admin") -> requests.Response:
    url = f"{settings.API_BASE_URL}/AssesstsMaster/vendors"
    payload = {
        "id": vendor_id,
        "Vendor_Name": vendor_name,
        "Contact_Person": contact_person,
        "Phone": phone,
        "Email": email,
        "Address": address,
        "GST": gst,
        "Supports_Amc": supports_amc
    }
    resp = requests.put(url, headers=get_auth_headers(user), json=payload, timeout=15)
    if resp.status_code in (404, 405):
        for alt_url in [f"{url}/{vendor_id}", f"{settings.API_BASE_URL}/AssesstsMaster/vendor/{vendor_id}", f"{settings.API_BASE_URL}/AssesstsMaster/vendor"]:
            resp = requests.put(alt_url, headers=get_auth_headers(user), json=payload, timeout=15)
            if resp.status_code in (200, 201, 204):
                break
    return resp


# ============================================================================
# 1. CATEGORY TESTS (GET, POST, PUT)
# ============================================================================

@pytest.mark.api
def test_get_categories():
    """Validates GET /api/AssesstsMaster/categories returns 200 and category list."""
    resp = get_categories()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    categories = resp.json()
    assert isinstance(categories, list), f"Expected list of categories, got {type(categories)}"
    assert len(categories) > 0, "Expected at least 1 category in database"
    
    sample = categories[0]
    assert "id" in sample or "category_Id" in sample, f"Category missing ID key: {sample}"
    assert "category_Name" in sample or "name" in sample, f"Category missing name key: {sample}"
    logger.info(f"Verified GET categories: {len(categories)} categories discovered.")


@pytest.mark.api
def test_post_category():
    """Validates POST /api/AssesstsMaster/categories creates a new category."""
    unique_name = f"Test_Cat_{int(time.time())}"
    resp = post_category(category_name=unique_name, description="Automated API Test Category")
    assert resp.status_code in (200, 201), f"Expected 200/201 on POST, got {resp.status_code}: {resp.text}"
    
    # Verify created category appears in GET list
    get_resp = get_categories()
    assert get_resp.status_code == 200
    matched = [c for c in get_resp.json() if c.get("category_Name", "").strip().lower() == unique_name.lower()]
    assert len(matched) > 0, f"Created category '{unique_name}' not found in GET response"
    logger.info(f"Verified POST category: '{unique_name}' created successfully (ID: {matched[0].get('id')}).")


@pytest.mark.api
def test_put_category():
    """Validates PUT /api/AssesstsMaster/categories updates an existing category."""
    unique_name = f"Test_Cat_Orig_{int(time.time())}"
    create_resp = post_category(category_name=unique_name, description="Original Description")
    assert create_resp.status_code in (200, 201)
    
    cats = get_categories().json()
    target = next((c for c in cats if c.get("category_Name", "").strip().lower() == unique_name.lower()), None)
    assert target is not None, "Target category for PUT test not found"
    cat_id = target.get("id") or target.get("category_Id")

    updated_name = f"Test_Cat_Updated_{int(time.time())}"
    updated_desc = "Updated Description via API Test"
    put_resp = put_category(category_id=cat_id, category_name=updated_name, description=updated_desc)
    assert put_resp.status_code in (200, 201, 204), f"Expected success on PUT, got {put_resp.status_code}: {put_resp.text}"
    logger.info(f"Verified PUT category ID {cat_id}: response status {put_resp.status_code}")


# ============================================================================
# 2. SUBCATEGORY TESTS (GET, POST, PUT)
# ============================================================================

@pytest.mark.api
def test_get_subcategories():
    """Validates GET /api/AssesstsMaster/subCategory returns 200 and subcategory list."""
    resp = get_subcategories()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    subcategories = resp.json()
    assert isinstance(subcategories, list), f"Expected list of subcategories, got {type(subcategories)}"
    assert len(subcategories) > 0, "Expected at least 1 subcategory in database"
    
    sample = subcategories[0]
    assert "id" in sample, f"SubCategory missing 'id' key: {sample}"
    assert "subCategory_Name" in sample or "name" in sample, f"SubCategory missing name key: {sample}"
    logger.info(f"Verified GET subcategories: {len(subcategories)} subcategories discovered.")


@pytest.mark.api
def test_post_subcategory():
    """Validates POST /api/AssesstsMaster/subCategory creates a new subcategory."""
    cats = get_categories().json()
    assert len(cats) > 0, "Need at least one category to create a subcategory"
    parent_cat_id = cats[0].get("id") or cats[0].get("category_Id")

    unique_sub_name = f"Test_Sub_{int(time.time())}"
    prefix = f"TS{str(int(time.time()))[-2:]}"
    resp = post_subcategory(
        category_id=parent_cat_id,
        subcategory_name=unique_sub_name,
        code_prefix=prefix,
        description="Automated API Test SubCategory"
    )
    assert resp.status_code in (200, 201), f"Expected 200/201 on POST, got {resp.status_code}: {resp.text}"
    logger.info(f"Verified POST subcategory: '{unique_sub_name}' created under Category ID {parent_cat_id}.")


@pytest.mark.api
def test_put_subcategory():
    """Validates PUT /api/AssesstsMaster/subCategory updates an existing subcategory."""
    cats = get_categories().json()
    parent_cat_id = cats[0].get("id") or cats[0].get("category_Id")

    unique_sub_name = f"Test_Sub_Orig_{int(time.time())}"
    prefix = f"TS{str(int(time.time()))[-2:]}"
    create_resp = post_subcategory(
        category_id=parent_cat_id,
        subcategory_name=unique_sub_name,
        code_prefix=prefix,
        description="Original SubCategory Description"
    )
    assert create_resp.status_code in (200, 201)

    subs = get_subcategories().json()
    target = next((s for s in subs if s.get("subCategory_Name", "").strip().lower() == unique_sub_name.lower()), None)
    assert target is not None, "Target subcategory for PUT test not found"
    sub_id = target.get("id")

    updated_sub_name = f"Test_Sub_Mod_{int(time.time())}"
    put_resp = put_subcategory(
        subcategory_id=sub_id,
        category_id=parent_cat_id,
        subcategory_name=updated_sub_name,
        code_prefix=prefix,
        description="Updated SubCategory Description via API"
    )
    assert put_resp.status_code in (200, 201, 204), f"Expected success on PUT, got {put_resp.status_code}: {put_resp.text}"
    logger.info(f"Verified PUT subcategory ID {sub_id}: response status {put_resp.status_code}")


# ============================================================================
# 3. VENDOR TESTS (GET, POST, PUT)
# ============================================================================

@pytest.mark.api
def test_get_vendors():
    """Validates GET /api/AssesstsMaster/vendors returns 200 and vendor list."""
    resp = get_vendors()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    vendors = resp.json()
    assert isinstance(vendors, list), f"Expected list of vendors, got {type(vendors)}"
    assert len(vendors) > 0, "Expected at least 1 vendor in database"
    
    sample = vendors[0]
    assert "id" in sample, f"Vendor missing 'id' key: {sample}"
    assert "vendor_Name" in sample or "name" in sample, f"Vendor missing name key: {sample}"
    logger.info(f"Verified GET vendors: {len(vendors)} vendors discovered.")


@pytest.mark.api
def test_post_vendor():
    """Validates POST /api/AssesstsMaster/vendors registers a new vendor."""
    ts = int(time.time())
    unique_vendor_name = f"Test_Vendor_{ts}"
    resp = post_vendor(
        vendor_name=unique_vendor_name,
        contact_person="Test Manager",
        phone=f"98{str(ts)[-8:]}",
        email=f"vendor_{ts}@example.com",
        address="Floor 4, Tech Park",
        gst=f"07AAAAA{str(ts)[-4:]}1Z5",
        supports_amc=True
    )
    assert resp.status_code in (200, 201), f"Expected 200/201 on POST, got {resp.status_code}: {resp.text}"
    logger.info(f"Verified POST vendor: '{unique_vendor_name}' created successfully.")


@pytest.mark.api
def test_put_vendor():
    """Validates PUT /api/AssesstsMaster/vendors updates an existing vendor."""
    ts = int(time.time())
    unique_vendor_name = f"Test_Vendor_Orig_{ts}"
    create_resp = post_vendor(
        vendor_name=unique_vendor_name,
        contact_person="Original Contact",
        phone=f"98{str(ts)[-8:]}",
        email=f"vendor_orig_{ts}@example.com",
        address="Original Address",
        gst=f"07AAAAA{str(ts)[-4:]}1Z5",
        supports_amc=True
    )
    assert create_resp.status_code in (200, 201)

    vendors = get_vendors().json()
    target = next((v for v in vendors if unique_vendor_name.lower() in str(v.get("vendor_Name", "")).lower()), None)
    assert target is not None, "Target vendor for PUT test not found"
    vendor_id = target.get("id")

    updated_vendor_name = f"Test_Vendor_Mod_{ts}"
    put_resp = put_vendor(
        vendor_id=vendor_id,
        vendor_name=updated_vendor_name,
        contact_person="Updated Contact Person",
        phone=f"99{str(ts)[-8:]}",
        email=f"vendor_mod_{ts}@example.com",
        address="Updated Suite 500",
        gst=f"07AAAAA{str(ts)[-4:]}1Z5",
        supports_amc=True
    )
    assert put_resp.status_code in (200, 201, 204), f"Expected success on PUT, got {put_resp.status_code}: {put_resp.text}"
    logger.info(f"Verified PUT vendor ID {vendor_id}: response status {put_resp.status_code}")
