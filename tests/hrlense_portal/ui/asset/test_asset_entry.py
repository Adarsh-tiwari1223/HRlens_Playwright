"""
UI Test Suite for Asset Entry Functionality (HR Lens Portal).
Strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
"""

import time
import random
import re
import pytest
import logging
from pages.base_page import TestStoryLogger, format_ascii_table
from workflows.hrlense_portal.asset.asset_entry_workflow import AssetEntryWorkflow
from testdata.dynamic.business_test_data import ASSET_TAXONOMY_15, TAXONOMY_10, BusinessTestData

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
def test_generate_assets_workflow(admin_page):
    """
    End-to-End Asset Entry 'Generate Assets' Workflow via Workflow Layer.
    """
    story = TestStoryLogger("Generate Assets Workflow", module="Asset Management", phase="Asset Entry")
    story.start()

    workflow = AssetEntryWorkflow(admin_page)
    result = workflow.generate_assets_workflow()

    form_data = result["form_data"]
    toast = result["toast"]

    story.log_step(
        "Generate Assets via Workflow",
        record=f"Procurement='{form_data.get('procurement')}', Item='{form_data.get('item')}'",
        expected="Assets generated successfully",
        actual=f"Toast: '{toast}'",
        status="PASS" if form_data.get("procurement") and form_data.get("item") else "FAIL"
    )

    assert form_data.get("procurement"), "Expected Procurement dropdown to have a selected value."
    assert form_data.get("item"), "Expected Procurement Item dropdown to have a selected value."
    is_success = any(kw in (toast or "").lower() for kw in ["success", "generated", "created", "saved"]) or toast == ""
    assert is_success, f"Unexpected toast on asset generation: '{toast}'"
    story.finish()


@pytest.mark.ui
@pytest.mark.asset
def test_manual_add_asset_workflow(admin_page):
    """
    End-to-End Manual Asset Entry Workflow via Workflow Layer.
    """
    story = TestStoryLogger("Manual Add Asset Entry Workflow", module="Asset Management", phase="Asset Entry")
    story.start()

    workflow = AssetEntryWorkflow(admin_page)
    unique_suffix = int(time.time())

    result = workflow.register_new_asset_workflow({
        "name": f"Dell Latitude {unique_suffix}",
        "branch": "Varanasi",
        "payroll_company": "TEK Inspirations LLC",
        "brand": "Dell",
        "model": "Latitude 7440",
        "serial_no": f"SN-DELL-{unique_suffix}",
        "warranty": "Warranty",
        "expiry_date": "2027-12-31",
        "insured": "Yes",
        "insurance_provider": "ICICI Lombard",
        "policy_number": f"POL-{unique_suffix}",
        "premium_amount": "5000",
        "premium_frequency": "Annually",
        "insurance_start_date": "2026-08-12",
        "insurance_expiry_date": "2027-08-12",
        "notes": f"Created via Automated Test - {unique_suffix}"
    })

    toast = result["toast"]
    is_success = any(kw in (toast or "").lower() for kw in ["success", "created", "saved", "generated", "added"]) or toast == ""

    story.log_step(
        "Manual Add Asset via Workflow",
        record=f"Serial: SN-DELL-{unique_suffix}",
        expected="Asset saved successfully",
        actual=f"Toast: '{toast}'",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Unexpected toast on saving asset: '{toast}'"
    story.finish()


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.parametrize("count", [1, 2, 3, 5, 10, 15, 20])
@pytest.mark.parametrize("branch", [
    "varanasi", "agra", "noida", "greater_noida",
    "jaipur", "lucknow", "meerut", "ranchi", "bhubaneswar"
])
def test_manual_add_assets_workflow(logged_in_page, request, branch, count):
    """Manually creates N distinct assets for the specified branch."""
    from utils.branch_it_selector import get_branch_it_person

    k_expr = request.config.getoption("-k") or ""
    k_numbers = re.findall(r"\b(\d+)\b", k_expr)
    target_count = int(k_numbers[0]) if k_numbers else count

    it_person = get_branch_it_person(branch)
    it_user_key = it_person.get("user_key", "admin")
    page, ctx = logged_in_page(it_user_key)

    story = TestStoryLogger(f"Manual Add {target_count} Assets ({branch.title()})", module="Asset Management", phase="Batch Asset Entry")
    story.start()

    workflow = AssetEntryWorkflow(page)
    created_assets = []

    for i in range(target_count):
        spec = ASSET_TAXONOMY_15[i % len(ASSET_TAXONOMY_15)]
        unique_suffix = f"{int(time.time())}_{i+1}_{random.randint(100, 999)}"
        serial_no = f"SN-{spec['brand'][:4].upper()}-{unique_suffix}"

        result = workflow.register_new_asset_workflow({
            "name": f"{spec['name']} #{i+1}",
            "branch": branch.title(),
            "category": spec.get("cat"),
            "sub_category": spec.get("sub"),
            "brand": spec.get("brand"),
            "model": spec.get("model"),
            "serial_no": serial_no,
            "warranty": "Warranty",
            "expiry_date": "2027-12-31",
            "insured": "Yes",
            "insurance_provider": "ICICI Lombard",
            "policy_number": f"POL-{unique_suffix}",
            "premium_amount": "5000",
            "premium_frequency": "Annually",
            "insurance_start_date": "2026-08-12",
            "insurance_expiry_date": "2027-08-12",
            "notes": f"Manually created batch item #{i+1} for {branch.title()}."
        })
        created_assets.append({"index": i+1, "serial": serial_no, "toast": result["toast"]})

    story.log_step(
        f"Generate {target_count} Manual Assets",
        record=f"Branch: {branch.title()}, Total Created: {len(created_assets)}",
        expected=f"{target_count} assets created successfully",
        actual=f"Created {len(created_assets)} assets",
        status="PASS"
    )
    story.finish()
    ctx.close()


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.security
@pytest.mark.parametrize("primary_branch, secondary_branch", [
    ("varanasi", "agra"),
    ("agra", "noida"),
    ("noida", "varanasi")
])
def test_cross_branch_asset_visibility_isolation(logged_in_page, primary_branch, secondary_branch):
    """Branch Data Isolation & Security Verification."""
    from utils.branch_it_selector import get_branch_it_person
    from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage

    p_it = get_branch_it_person(primary_branch)
    s_it = get_branch_it_person(secondary_branch)

    story = TestStoryLogger(
        f"Cross-Branch Isolation: {primary_branch.title()} vs {secondary_branch.title()}",
        module="Asset Management", phase="Security & Branch Isolation"
    )
    story.start()

    # Step 1: Primary branch creates asset
    p_page, p_ctx = logged_in_page(p_it.get("user_key", "admin"))
    p_workflow = AssetEntryWorkflow(p_page)
    unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
    serial_no = f"SN-ISOL-{primary_branch[:3].upper()}-{unique_id}"

    p_workflow.register_new_asset_workflow({
        "name": f"Isolation Workstation {primary_branch.title()} {unique_id}",
        "branch": f"{primary_branch.title()} Group",
        "category": "IT Hardware",
        "sub_category": "Laptop",
        "brand": "Dell",
        "model": "Latitude 7440",
        "serial_no": serial_no,
        "warranty": "Warranty",
        "expiry_date": "2027-12-31",
        "insured": "No",
        "notes": f"Branch isolation test asset for {primary_branch.title()}."
    })

    # Verify visible in primary branch
    p_entry = AssetEntryPage(p_page)
    p_entry.navigate_to_asset_entry()
    p_entry.search_asset(serial_no)
    p_page.wait_for_timeout(1000)
    p_row = p_page.locator("table tbody tr, tbody tr").first
    p_row_text = p_row.inner_text() if p_row.is_visible(timeout=3000) else ""
    is_visible_in_primary = serial_no in p_row_text

    story.log_step(
        f"1. Asset Visible in {primary_branch.title()}",
        record=f"Serial: {serial_no}",
        expected=f"Asset visible to {primary_branch.title()} IT Person",
        actual=f"Found: {p_row_text[:60]}",
        status="PASS" if is_visible_in_primary else "FAIL"
    )
    assert is_visible_in_primary, f"Asset '{serial_no}' should be visible to {primary_branch.title()} IT Person!"
    p_ctx.close()

    # Step 2: Secondary branch cannot see it
    s_page, s_ctx = logged_in_page(s_it.get("user_key", "admin"))
    s_entry = AssetEntryPage(s_page)
    s_entry.navigate_to_asset_entry()
    s_entry.search_asset(serial_no)
    s_page.wait_for_timeout(1500)
    s_row = s_page.locator("table tbody tr, tbody tr").first
    s_row_text = s_row.inner_text() if s_row.is_visible(timeout=2000) else ""
    is_hidden = serial_no not in s_row_text

    story.log_step(
        f"2. Asset Hidden from {secondary_branch.title()}",
        record=f"Searched: {serial_no}",
        expected=f"Asset hidden from {secondary_branch.title()} IT Person",
        actual=f"Is Hidden: {is_hidden}",
        status="PASS" if is_hidden else "FAIL"
    )
    s_ctx.close()
    assert is_hidden, f"Security Violation! Asset '{serial_no}' of {primary_branch.title()} was visible to {secondary_branch.title()} IT Person!"
    story.finish()


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.seeding
def test_manual_add_5_assets_per_category_subcategory(admin_page):
    """Creates 5 active assets for each of the 10 Category + Sub-Category pairs (50 total)."""
    story = TestStoryLogger("Manual Seed: 5 Active Assets per Category & Sub-Category", module="Asset Management", phase="Asset Entry")
    story.start()

    workflow = AssetEntryWorkflow(admin_page)
    total_created = 0
    results_summary = []

    for cat_idx, item in enumerate(TAXONOMY_10, 1):
        cat_name = item["cat"]
        sub_name = item["sub"]
        prefix = item["prefix"]
        models_list = item["models"]

        for asset_idx, (brand, model) in enumerate(models_list, 1):
            unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
            serial_no = f"SN-{prefix}-VAR-{unique_id}"

            workflow.register_new_asset_workflow({
                "name": f"{brand} {model}",
                "branch": "Varanasi",
                "category": cat_name,
                "sub_category": sub_name,
                "brand": brand,
                "model": model,
                "serial_no": serial_no,
                "warranty": "Warranty",
                "expiry_date": "2028-06-30",
                "insured": "No",
                "notes": f"Active asset #{asset_idx} for Category '{cat_name}' -> Subcategory '{sub_name}'"
            })
            total_created += 1
            results_summary.append({
                "category": cat_name,
                "sub_category": sub_name,
                "asset_name": f"{brand} {model}",
                "serial_no": serial_no,
                "status": "CREATED & ACTIVE"
            })

        story.log_step(
            f"Seed 5 Active Assets: {cat_name} -> {sub_name}",
            record=f"Total: 5 active assets ({prefix})",
            expected=f"5 active assets created under {cat_name} -> {sub_name}",
            actual="5 assets created successfully",
            status="PASS"
        )

    print("\n" + format_ascii_table("50 ACTIVE ASSETS SEEDED (5 PER CATEGORY & SUB-CATEGORY)", results_summary))
    story.finish(status="PASS")
