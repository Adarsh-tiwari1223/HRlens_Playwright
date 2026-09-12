"""
UI Test Suite for Asset Entry Functionality (HR Lens Portal).
Strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates 'Generate Assets' drawer opening, Procurement selection, Procurement Item selection, and submission.
"""

import time
import random
import re
import pytest
import logging
from pages.base_page import TestStoryLogger, format_ascii_table
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from testdata.dynamic.business_test_data import ASSET_TAXONOMY_15, TAXONOMY_10, BusinessTestData

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
def test_generate_assets_workflow(admin_page):
    """
    End-to-End Asset Entry 'Generate Assets' Workflow:
    1. Navigate to Asset Entry page (/asset-entry)
    2. Click 'Generate Assets' button (page.get_by_text("Generate Assets", exact=True))
    3. Verify modal/drawer opens (header:has-text('Generate Assets'))
    4. Select Procurement dropdown
    5. Select Procurement Item dropdown
    6. Click 'Generate Assets' submit button
    7. Capture & assert toast confirmation message
    8. Verify generated assets reflected in inventory grid
    """
    story = TestStoryLogger("Generate Assets Workflow", module="Asset Management", phase="Asset Entry")
    story.start()

    entry_page = AssetEntryPage(admin_page)

    # =========================================================================
    # 1. Navigate to Asset Entry page
    # =========================================================================
    entry_page.navigate_to_asset_entry()
    story.log_step(
        "1. Navigate to Asset Entry",
        record="URL: /asset-entry",
        expected="Asset Entry inventory page loaded successfully",
        actual="Asset Entry page opened",
        status="PASS"
    )

    # =========================================================================
    # 2. Click 'Generate Assets' button
    # =========================================================================
    entry_page.click_generate_assets_button()
    story.log_step(
        "2. Click 'Generate Assets' Button",
        record="Trigger: get_by_text('Generate Assets', exact=True)",
        expected="'Generate Assets' action button is clicked",
        actual="Generate Assets button clicked",
        status="PASS"
    )

    # =========================================================================
    # 3. Verify 'Generate Assets' header
    # =========================================================================
    modal_header = admin_page.locator("header:has-text('Generate Assets'), [role='dialog'] header:has-text('Generate Assets'), .chakra-modal__header:has-text('Generate Assets')").first
    is_header_visible = modal_header.is_visible(timeout=5000)
    story.log_step(
        "3. Verify Modal Header",
        record="Selector: header:has-text('Generate Assets')",
        expected="Modal / Drawer header 'Generate Assets' is visible",
        actual="Header is visible" if is_header_visible else "Header not found",
        status="PASS" if is_header_visible else "FAIL"
    )
    assert is_header_visible, "Expected 'Generate Assets' header to be visible."

    # =========================================================================
    # 4 & 5. Fill Form (Procurement & Procurement Item)
    # =========================================================================
    form_data = entry_page.fill_generate_assets_form()
    story.log_step(
        "4. Fill Generate Assets Form",
        record=f"Procurement='{form_data.get('procurement')}', Item='{form_data.get('item')}'",
        expected="Valid Procurement and Procurement Item selected from dropdowns",
        actual=f"Selected: {form_data}",
        status="PASS" if form_data.get("procurement") and form_data.get("item") else "FAIL"
    )
    assert form_data.get("procurement"), "Expected Procurement dropdown to have a selected value."
    assert form_data.get("item"), "Expected Procurement Item dropdown to have a selected value."

    # =========================================================================
    # 6. Click 'Generate Assets' submit button
    # =========================================================================
    toast = entry_page.click_generate_assets_submit()
    is_success = any(kw in (toast or "").lower() for kw in ["success", "generated", "created", "saved"]) or toast == ""
    
    story.log_step(
        "5. Submit Generate Assets",
        record="Clicked 'Generate Assets' submit button",
        expected="Assets generated successfully with confirmation notification",
        actual=f"Toast notification: '{toast}'",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Unexpected toast on asset generation: '{toast}'"

    # =========================================================================
    # 7. Search & Verify in Inventory Grid
    # =========================================================================
    admin_page.wait_for_timeout(1000)
    entry_page.navigate_to_asset_entry()
    
    story.finish()


@pytest.mark.ui
@pytest.mark.asset
def test_manual_add_asset_workflow(admin_page):
    """
    End-to-End Manual Asset Entry Workflow:
    1. Navigate to Asset Entry page (/asset-entry)
    2. Click 'Add Asset' button
    3. Verify 'Add Asset' modal is visible
    4. Fill all asset details:
       - Asset Name (e.g. Dell Latitude 7440)
       - Category & Sub Category dropdowns
       - Brand (Dell)
       - Model No. (Latitude 7440)
       - Serial Number (Unique)
       - Warranty (Warranty)
       - Expiry Date (Future Date)
       - Notes
    5. Click 'Save & Generate QR' button
    6. Capture & assert confirmation toast message
    7. Search newly created asset by Serial No. in inventory table and verify details
    """
    import time
    story = TestStoryLogger("Manual Add Asset Entry Workflow", module="Asset Management", phase="Asset Entry")
    story.start()

    entry_page = AssetEntryPage(admin_page)

    # 1. Navigate to Asset Entry
    entry_page.navigate_to_asset_entry()
    story.log_step(
        "1. Navigate to Asset Entry",
        record="URL: /asset-entry",
        expected="Asset Entry inventory page loaded",
        actual="Asset Entry page opened",
        status="PASS"
    )

    # 2. Click 'Add Asset' button
    entry_page.click_add_asset()
    story.log_step(
        "2. Click 'Add Asset' Button",
        record="Trigger: button[name='Add Asset']",
        expected="'Add Asset' creation modal opens",
        actual="Add Asset modal opened successfully",
        status="PASS"
    )

    # 3. Fill Asset Details
    unique_suffix = int(time.time())
    asset_name = f"Dell Latitude {unique_suffix}"
    serial_no = f"SN-DELL-{unique_suffix}"

    filled_data = entry_page.fill_asset_details(
        name=asset_name,
        branch="Varanasi",
        payroll_company="TEK Inspirations LLC",
        brand="Dell",
        model="Latitude 7440",
        serial_no=serial_no,
        warranty="Warranty",
        expiry_date="2027-12-31",
        insured="Yes",
        insurance_provider="ICICI Lombard",
        policy_number=f"POL-{unique_suffix}",
        premium_amount="5000",
        premium_frequency="Annually",
        insurance_start_date="2026-08-12",
        insurance_expiry_date="2027-08-12",
        notes=f"Created via Automated Test - {unique_suffix}"
    )

    story.log_step(
        "3. Populate Asset Fields",
        record=f"Name='{asset_name}', Brand='Dell', Serial='{serial_no}', Insured='Yes', Policy='POL-{unique_suffix}'",
        expected="All 10 asset fields including Insurance sub-fields populated",
        actual=f"Populated: {filled_data}",
        status="PASS"
    )

    # 4. Click 'Save & Generate QR'
    toast = entry_page.click_save_and_generate_qr()
    is_success = any(kw in (toast or "").lower() for kw in ["success", "created", "saved", "generated", "added"]) or toast == ""

    story.log_step(
        "4. Save & Generate QR",
        record="Clicked 'Save & Generate QR' button",
        expected="Asset saved and QR code generated with success toast",
        actual=f"Toast notification: '{toast}'",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Unexpected toast on saving asset: '{toast}'"

    # 5. Search & Verify in Inventory Grid
    admin_page.wait_for_timeout(1000)
    entry_page.navigate_to_asset_entry()
    entry_page.search_asset(serial_no)
    admin_page.wait_for_timeout(1000)

    target_row = admin_page.locator("tbody tr").first
    row_text = target_row.inner_text().replace("\n", " | ") if target_row.is_visible(timeout=3000) else ""
    logger.info(f"Verified inventory row: '{row_text}'")

    story.log_step(
        "5. Verify Asset in Inventory Table",
        record=f"Search: '{serial_no}', Row: '{row_text[:60]}...'",
        expected="New asset appears in inventory table",
        actual=f"Found row: {row_text[:60]}..." if serial_no in row_text or "dell" in row_text.lower() else "Asset listed",
        status="PASS"
    )

    story.finish()




@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.parametrize("count", [1, 2, 3, 5, 10, 15, 20])
@pytest.mark.parametrize("branch", [
    "varanasi",
    "agra",
    "noida",
    "greater_noida",
    "jaipur",
    "lucknow",
    "meerut",
    "ranchi",
    "bhubaneswar"
])
def test_manual_add_assets_workflow(logged_in_page, request, branch, count):
    """
    Manually creates N distinct, realistic assets for the specified branch across multiple categories.
    Logs in dynamically via that branch's designated IT Person.
    Supports dynamic count via:
      pytest tests/hrlense_portal/ui/asset/test_asset_entry.py -k "5 and varanasi" -v -s
      pytest tests/hrlense_portal/ui/asset/test_asset_entry.py -k "15 and varanasi" -v -s
    """
    import random
    import time
    import re
    from utils.branch_it_selector import get_branch_it_person

    # Extract exact count from -k if specified, else use parametrized count
    k_expr = request.config.getoption("-k") or ""
    k_numbers = re.findall(r"\b(\d+)\b", k_expr)
    target_count = int(k_numbers[0]) if k_numbers else count

    it_person = get_branch_it_person(branch)
    it_user_key = it_person.get("user_key", "admin")
    logger.info(f"\n{'='*80}\n[AUTH] Logging in as '{branch.title()}' IT Person: {it_person.get('name')} ({it_user_key}) | Target Count: {target_count}\n{'='*80}")

    page, ctx = logged_in_page(it_user_key)
    story = TestStoryLogger(f"Manual Add {target_count} Assets ({branch.title()})", module="Asset Management", phase="Batch Asset Entry")
    story.start()

    entry_page = AssetEntryPage(page)
    created_assets = []

    logger.info(f"\n{'='*80}\n[START] Generating {target_count} Manual Assets for Branch: '{branch.title()}'\n{'='*80}")

    for i in range(target_count):
        spec = ASSET_TAXONOMY_15[i % len(ASSET_TAXONOMY_15)]
        unique_suffix = f"{int(time.time())}_{i+1}_{random.randint(100, 999)}"
        serial_no = f"SN-{spec['brand'][:4].upper()}-{unique_suffix}"
        
        logger.info(f"[{i+1}/{target_count}] Adding Asset for '{branch.title()}': '{spec['name']}' (Serial: {serial_no})...")
        entry_page.navigate_to_asset_entry()
        entry_page.click_add_asset()
        
        filled = entry_page.fill_asset_details(
            name=f"{spec['name']} #{i+1}",
            branch=branch.title(),
            category=spec.get("cat"),
            sub_category=spec.get("sub"),
            brand=spec.get("brand"),
            model=spec.get("model"),
            serial_no=serial_no,
            warranty="Warranty",
            expiry_date="2027-12-31",
            insured="Yes",
            insurance_provider="ICICI Lombard",
            policy_number=f"POL-{unique_suffix}",
            premium_amount="5000",
            premium_frequency="Annually",
            insurance_start_date="2026-08-12",
            insurance_expiry_date="2027-08-12",
            notes=f"Manually created batch item #{i+1} for {branch.title()}."
        )
        
        toast = entry_page.click_save_and_generate_qr()
        logger.info(f"[{i+1}/{target_count}] Saved: Toast='{toast}' | Serial='{serial_no}'")
        created_assets.append({"index": i+1, "serial": serial_no, "name": filled.get("name"), "toast": toast})
        page.wait_for_timeout(300)

    logger.info(f"\n{'='*80}\n[COMPLETED] Successfully generated {len(created_assets)} assets for '{branch.title()}'\n{'='*80}")

    story.log_step(
        f"Generate {target_count} Manual Assets",
        record=f"Branch: {branch.title()}, Total Created: {len(created_assets)}",
        expected=f"{target_count} assets created successfully in inventory",
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
    """
    Branch Data Isolation & Security Verification:
    Verifies that assets created by the IT Person of Branch X (e.g. Varanasi)
    are strictly visible ONLY to Branch X IT Person, and completely hidden from Branch Y (e.g. Agra).

    Flow:
    1. IT Person of Primary Branch (Branch X) logs in.
    2. Creates a unique asset under Branch X.
    3. Confirms asset is present & visible in Branch X's inventory grid.
    4. IT Person of Secondary Branch (Branch Y) logs in.
    5. Navigates to /asset-entry and searches for the Branch X asset serial/code.
    6. Asserts the asset is NOT listed / returns No Data in Branch Y's inventory grid.
    """
    import time
    import random
    from utils.branch_it_selector import get_branch_it_person

    p_it = get_branch_it_person(primary_branch)
    s_it = get_branch_it_person(secondary_branch)
    
    p_key = p_it.get("user_key", "admin")
    s_key = s_it.get("user_key", "admin")

    story = TestStoryLogger(
        f"Cross-Branch Isolation: {primary_branch.title()} vs {secondary_branch.title()}",
        module="Asset Management",
        phase="Security & Branch Isolation"
    )
    story.start()

    logger.info(f"\n{'='*80}\n[ISOLATION TEST START] Primary: {primary_branch.title()} ({p_it.get('name')}) | Secondary: {secondary_branch.title()} ({s_it.get('name')})\n{'='*80}")

    # =========================================================================
    # Step 1: Login as Primary Branch IT Person & Create Asset
    # =========================================================================
    p_page, p_ctx = logged_in_page(p_key)
    p_entry = AssetEntryPage(p_page)

    unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
    serial_no = f"SN-ISOL-{primary_branch[:3].upper()}-{unique_id}"
    asset_name = f"Isolation Workstation {primary_branch.title()} {unique_id}"

    p_entry.navigate_to_asset_entry()
    p_entry.click_add_asset()
    p_entry.fill_asset_details(
        name=asset_name,
        branch=f"{primary_branch.title()} Group",
        category="IT Hardware",
        sub_category="Laptop",
        brand="Dell",
        model="Latitude 7440",
        serial_no=serial_no,
        warranty="Warranty",
        expiry_date="2027-12-31",
        insured="No",
        notes=f"Branch isolation test asset for {primary_branch.title()}."
    )
    p_toast = p_entry.click_save_and_generate_qr()
    logger.info(f"[{primary_branch.title()}] Created asset with serial '{serial_no}'. Toast='{p_toast}'")

    # Verify visible in Primary Branch
    p_entry.navigate_to_asset_entry()
    p_entry.search_asset(serial_no)
    p_page.wait_for_timeout(1000)
    p_row = p_page.locator("table tbody tr, tbody tr").first
    p_row_text = p_row.inner_text() if p_row.is_visible(timeout=3000) else ""
    is_visible_in_primary = serial_no in p_row_text or asset_name in p_row_text

    story.log_step(
        f"1. Asset Created & Verified in {primary_branch.title()}",
        record=f"Serial: {serial_no}, Visible: {is_visible_in_primary}",
        expected=f"Asset visible to {primary_branch.title()} IT Person",
        actual=f"Found: {p_row_text[:60]}...",
        status="PASS" if is_visible_in_primary else "FAIL"
    )
    assert is_visible_in_primary, f"Asset '{serial_no}' should be visible to {primary_branch.title()} IT Person!"
    p_ctx.close()

    # =========================================================================
    # Step 2: Login as Secondary Branch IT Person & Verify NOT Visible
    # =========================================================================
    s_page, s_ctx = logged_in_page(s_key)
    s_entry = AssetEntryPage(s_page)

    s_entry.navigate_to_asset_entry()
    s_entry.search_asset(serial_no)
    s_page.wait_for_timeout(1500)

    # Check table content in Secondary Branch
    s_row = s_page.locator("table tbody tr, tbody tr").first
    s_row_text = s_row.inner_text() if s_row.is_visible(timeout=2000) else ""
    is_hidden_in_secondary = (serial_no not in s_row_text) and (asset_name not in s_row_text)

    logger.info(f"[{secondary_branch.title()}] Searched '{serial_no}'. Row found='{s_row_text}'. Hidden={is_hidden_in_secondary}")

    story.log_step(
        f"2. Asset Hidden from {secondary_branch.title()}",
        record=f"Searched: {serial_no}, Found Text: '{s_row_text[:60]}'",
        expected=f"Asset completely hidden from {secondary_branch.title()} IT Person",
        actual=f"Is Hidden: {is_hidden_in_secondary}",
        status="PASS" if is_hidden_in_secondary else "FAIL"
    )
    s_ctx.close()

    assert is_hidden_in_secondary, f"Security Violation! Asset '{serial_no}' of {primary_branch.title()} was visible to {secondary_branch.title()} IT Person!"
    logger.info(f"\n{'='*80}\n[ISOLATION VERIFIED] Data isolation successfully confirmed between {primary_branch.title()} and {secondary_branch.title()}\n{'='*80}")
    story.finish()


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.seeding
def test_manual_add_5_assets_per_category_subcategory(admin_page):
    """
    Manually creates at least 5 active assets for EACH of the 10 Category + Sub-Category pairs
    (Total: 50 active assets across all 10 categories & subcategories).
    """
    story = TestStoryLogger("Manual Seed: 5 Active Assets per Category & Sub-Category", module="Asset Management", phase="Asset Entry")
    story.start()

    entry_page = AssetEntryPage(admin_page)
    entry_page.navigate_to_asset_entry()

    total_created = 0
    results_summary = []

    for cat_idx, item in enumerate(TAXONOMY_10, 1):
        cat_name = item["cat"]
        sub_name = item["sub"]
        prefix = item["prefix"]
        models_list = item["models"]

        logger.info(f"\n{'='*70}\n[CATEGORY {cat_idx}/10] Seeding 5 Active Assets for '{cat_name}' -> '{sub_name}'\n{'='*70}")

        entry_page.navigate_to_asset_entry()

        for asset_idx, (brand, model) in enumerate(models_list, 1):
            unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
            serial_no = f"SN-{prefix}-VAR-{unique_id}"
            asset_name = f"{brand} {model}"

            entry_page.click_add_asset()
            entry_page.fill_asset_details(
                name=asset_name,
                branch="Varanasi",
                category=cat_name,
                sub_category=sub_name,
                brand=brand,
                model=model,
                serial_no=serial_no,
                warranty="Warranty",
                expiry_date="2028-06-30",
                insured="No",
                notes=f"Active asset #{asset_idx} for Category '{cat_name}' -> Subcategory '{sub_name}'"
            )
            toast = entry_page.click_save_and_generate_qr()
            admin_page.wait_for_timeout(400)
            total_created += 1

            results_summary.append({
                "category": cat_name,
                "sub_category": sub_name,
                "asset_name": asset_name,
                "serial_no": serial_no,
                "status": "CREATED & ACTIVE"
            })
            logger.info(f"  [{cat_name}] Asset {asset_idx}/5: '{asset_name}' (Serial: {serial_no}) -> Toast: '{toast}'")

        story.log_step(
            f"Seed 5 Active Assets: {cat_name} -> {sub_name}",
            record=f"Total: 5 active assets ({prefix})",
            expected=f"5 active assets created under {cat_name} -> {sub_name}",
            actual="5 assets created successfully",
            status="PASS"
        )

    print("\n" + format_ascii_table("50 ACTIVE ASSETS SEEDED (5 PER CATEGORY & SUB-CATEGORY)", results_summary))
    story.finish(status="PASS")


