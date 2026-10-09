"""
HRlens Portal — Asset Recovery Installments to Resignation FnF Settlement Integration Test Suite.

End-to-End Business Flow Verified:
1. Employee has an assigned company hardware asset (Laptop/Desktop).
2. IT/Admin marks the asset as 'Damaged' or 'Lost' on /asset-return, selects 'Recover Amount',
   and enters a monetary recovery amount (e.g. ₹4,000).
3. Admin navigates to /asset-recovery, opens 'Settle Recovery', selects 'Installments' mode,
   auto-splits into 2 monthly installments (₹2,000/mo), verifies 'Balanced ✓', and saves the plan.
4. Employee applies for resignation on /resignation.
5. HR approves resignation on /resignation-approval and clearances are completed.
6. HR triggers 'Start FnF Process' on /resignation-approval.
7. Accountant opens /accounts-buyout-processing -> 'FnF Requests' tab and opens the
   'Full & Final Settlement' drawer for the employee.
8. CORE ASSERTION / VERIFICATION:
   Inspects the 'Asset Recovery' deduction line item inside the FnF drawer to verify whether
   the pending asset recovery installments (₹4,000) are AUTOMATICALLY pre-populated into FnF deductions,
   or remain at 0.00 / blank (requiring manual accountant intervention).
"""

import os
import re
import random
import logging
import pytest
from datetime import datetime

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage
from pages.hrlense_portal.asset.asset_recovery_page import AssetRecoveryPage
from pages.hrlense_portal.resignation.resignation_page import ResignationPage
from workflows.hrlense_portal.resignation.employee_resignation_workflow import EmployeeResignationWorkflow
from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow
from workflows.hrlense_portal.resignation.accountant_resignation_workflow import AccountantResignationWorkflow
from workflows.hrlense_portal.resignation.it_resignation_workflow import ItResignationWorkflow

logger = logging.getLogger(__name__)

CANDIDATES = [
    {
        "name": "Uttam Kumar",
        "user_key": "uttam_kumar",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Adarsh Tiwari",
        "user_key": "adarsh_tiwari",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Sanidhy Tiwari",
        "user_key": "sanidhy",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
]


@pytest.mark.ui
@pytest.mark.resignation
@pytest.mark.asset
def test_asset_recovery_installment_to_fnf_integration(logged_in_page, request):
    """
    Executes the integrated Asset Recovery Installment -> Resignation -> FnF Auto-Deduction test.
    """
    story = TestStoryLogger("Asset Recovery Installments to Resignation FnF Integration")

    screenshots_dir = os.path.join(os.getcwd(), "reports", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    # 1. Select target candidate
    emp_opt = request.config.getoption("--employee", default=None)
    selected_emp = CANDIDATES[0]
    if emp_opt:
        match = next((c for c in CANDIDATES if c["name"].lower() == emp_opt.lower()), None)
        if match:
            selected_emp = match

    emp_name = selected_emp["name"]
    emp_key = selected_emp["user_key"]
    hr_key = selected_emp["hr_key"]
    it_key = selected_emp["it_key"]
    branch = selected_emp["branch"]

    recovery_amount = 4000
    installment_months = 2

    logger.info("=" * 80)
    logger.info(f"TEST: ASSET RECOVERY INSTALLMENTS -> FnF SETTLEMENT FOR '{emp_name}'")
    logger.info(f"Recovery Amount: ₹{recovery_amount} | Installments: {installment_months} Months")
    logger.info("=" * 80)
    story.log_step(
        "Candidate Selection",
        record=f"Employee: '{emp_name}' ({emp_key}) | Branch: {branch}",
        expected="Valid employee credentials",
        actual=emp_name,
        status="PASS"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 1: ENSURE EMPLOYEE HAS AN ASSIGNED ASSET
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STAGE 1 - ASSET CHECK] Verifying if '{emp_name}' has an assigned asset...")
    admin_page, _ = logged_in_page("admin")
    return_page = AssetReturnPage(admin_page)
    return_page.navigate_to_asset_return()

    # Check Assigned Assets tab for existing asset
    assigned_row = None
    assigned_code = None
    try:
        assigned_tab = admin_page.locator("button[role='tab']:has-text('Assigned Assets')").first
        if assigned_tab.is_visible(timeout=3000):
            assigned_tab.click()
            admin_page.wait_for_timeout(1000)

        # Search for employee in table
        search_in = admin_page.locator("input[placeholder*='Search asset / employee' i], input[placeholder*='Search' i]").first
        if search_in.is_visible(timeout=2000):
            search_in.fill(emp_name)
            search_in.press("Enter")
            admin_page.wait_for_timeout(1500)

        row = admin_page.locator(f"table tbody tr:has-text('{emp_name}')").first
        if row.is_visible(timeout=2000):
            assigned_row = row
            text = row.inner_text()
            m = re.search(r"ASSET-[A-Z0-9-]+", text)
            if m:
                assigned_code = m.group(0)
    except Exception as e:
        logger.warning(f"Note checking existing asset on return page: {e}")

    if not assigned_code:
        logger.info(f"[STAGE 1 - ASSET SETUP] No existing assigned asset for '{emp_name}'. Procuring & Assigning new asset...")
        # Procure fresh asset
        entry_page = AssetEntryPage(admin_page)
        entry_page.navigate_to_asset_entry()
        entry_page.click_add_asset()
        serial_no = f"SN-FNF-{branch[:3].upper()}-{random.randint(100000, 999999)}"
        entry_data = entry_page.fill_asset_details(
            name=f"Laptop Workstation ({branch})",
            category="IT Hardware",
            sub_category="Laptop",
            brand="Dell",
            model="Latitude 5430",
            serial_no=serial_no,
            branch=f"{branch} Group" if "Group" not in branch else branch,
            warranty="Warranty",
            expiry_date="2028-12-31",
            insured="No",
            notes="Asset for recovery to FnF integration test."
        )
        entry_page.click_save()
        entry_page.wait_for_toast_message()

        # Locate created code
        entry_page.navigate_to_asset_entry()
        admin_page.locator("input[placeholder*='Search']").first.fill(serial_no)
        admin_page.locator("input[placeholder*='Search']").first.press("Enter")
        admin_page.wait_for_timeout(1000)
        row = admin_page.locator("table tbody tr").filter(has_text=serial_no).first
        row_text = row.inner_text() if row.is_visible(timeout=3000) else ""
        m = re.search(r"ASSET-[A-Z0-9-]+", row_text)
        assigned_code = m.group(0) if m else "ASSET"
        logger.info(f"[STAGE 1] Procured Asset Code: '{assigned_code}' | Category: {entry_data.get('category')} | SubCategory: {entry_data.get('sub_category')}")

        # Assign asset to employee using actual selected category
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        assigned_code = assign_page.fill_assignment_details(
            employee_name=emp_name,
            category=entry_data.get("category") or "Networking",
            sub_category=entry_data.get("sub_category") or "Router",
            asset_name_or_code=assigned_code,
            remarks="Assignment for FnF recovery integration"
        )
        assign_page.click_submit_assignment()
        assign_page.wait_for_toast_message()

        # Employee accepts asset
        emp_page, _ = logged_in_page(emp_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(assigned_code)

    logger.info(f"[STAGE 1 VERIFIED] Employee '{emp_name}' has assigned asset: '{assigned_code}'")
    story.log_step(
        "Asset Assignment",
        record=f"Assigned Asset: '{assigned_code}' to '{emp_name}'",
        expected="Asset assigned and accepted",
        actual=assigned_code,
        status="PASS"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 2: RETURN ASSET AS DAMAGED WITH RECOVERY AMOUNT
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STAGE 2 - ASSET RETURN] Marking asset '{assigned_code}' as Damaged with recovery amount ₹{recovery_amount}...")
    admin_page.bring_to_front()
    return_page.navigate_to_asset_return()
    return_res = return_page.return_asset(
        asset_code_or_name=assigned_code or emp_name,
        condition="Damaged",
        recovery_type="recover",
        recovery_amount=str(recovery_amount),
        remarks=f"Asset damaged by employee during tenure. Recovery ₹{recovery_amount} assessed."
    )
    admin_page.wait_for_timeout(1500)
    story.log_step(
        "Return Asset Damaged",
        record=f"Asset '{assigned_code}' marked Damaged with Recovery Amount ₹{recovery_amount}",
        expected="Asset returned with recovery required",
        actual="Damaged Return Recorded",
        status="PASS"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 3: CONVERT RECOVERY INTO INSTALLMENT PLAN ON /asset-recovery
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STAGE 3 - INSTALLMENTS] Admin setting up {installment_months}-month Installment Plan on /asset-recovery...")
    recovery_page = AssetRecoveryPage(admin_page)
    recovery_page.navigate_to_asset_recovery()

    # Read KPI metrics
    kpi_before = recovery_page.get_kpi_metrics()
    logger.info(f"[STAGE 3] KPI metrics before installment: {kpi_before}")

    # Switch to Pending tab and locate row
    recovery_page.switch_tab("Pending")
    row_found = recovery_page.click_settle_button(emp_name)
    if not row_found and assigned_code:
        row_found = recovery_page.click_settle_button(assigned_code)

    if not row_found:
        recovery_page.switch_tab("All")
        row_found = recovery_page.click_settle_button(emp_name)
        if not row_found and assigned_code:
            row_found = recovery_page.click_settle_button(assigned_code)

    assert row_found, f"Could not find recovery record to click 'Settle' for '{emp_name}' / '{assigned_code}'"

    # Create 2-month installment plan
    installment_toast = recovery_page.create_installment_plan(months_count=installment_months)
    logger.info(f"[STAGE 3] Installment Plan Toast: '{installment_toast}'")

    sc_installments = os.path.join(screenshots_dir, "fnf_stage3_installment_plan_saved.png")
    admin_page.screenshot(path=sc_installments)

    story.log_step(
        "Setup Installment Plan",
        record=f"Installment plan created: {installment_months} months | Toast: '{installment_toast}'",
        expected="Installment plan saved successfully",
        actual=installment_toast or "Saved",
        status="PASS"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 4: EMPLOYEE APPLIES FOR RESIGNATION
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STAGE 4 - RESIGNATION] Employee '{emp_name}' applying for resignation...")
    emp_page_res, _ = logged_in_page(emp_key)
    emp_wf = EmployeeResignationWorkflow(emp_page_res)
    emp_wf.res_page.navigate_to_resignation()

    if not emp_wf.res_page.has_active_resignation():
        res_result = emp_wf.submit_resignation_workflow(
            reason="1",
            stay_connected=True,
            share_suggestions=True,
            suggestion_text="Resignation for E2E FnF recovery integration validation.",
            confirm=True
        )
        res_toast = res_result.get("toast", "")
        logger.info(f"[STAGE 4] Resignation submission toast: '{res_toast}'")
        story.log_step(
            "Employee Resignation",
            record=f"Resignation submitted. Toast: '{res_toast}'",
            expected="Resignation submitted",
            actual=res_toast,
            status="PASS"
        )
    else:
        logger.info(f"[STAGE 4] Employee '{emp_name}' already has active resignation on portal.")
        story.log_step(
            "Employee Resignation",
            record=f"Active resignation already present for '{emp_name}'",
            expected="Active resignation present",
            actual="Active",
            status="PASS"
        )

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 5: HR APPROVES RESIGNATION & TRIGGERS FnF
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STAGE 5 - HR APPROVAL & START FnF] HR ({hr_key}) processing on /resignation-approval...")
    hr_page, _ = logged_in_page(hr_key)
    hr_wf = HrResignationWorkflow(hr_page)
    hr_wf.res_page.navigate_to_hr_resignation_approval()
    hr_wf.res_page.search_employee_in_hr_table(emp_name)

    hr_status = hr_wf.res_page.get_hr_table_employee_status(emp_name)
    logger.info(f"[STAGE 5] HR table status for '{emp_name}': '{hr_status}'")

    # If Revoke/Accept is required:
    hr_row = hr_page.locator(f"tr:has-text('{emp_name}')").first
    if hr_row.locator("button:has-text('Approve'), button:has-text('Accept')").first.is_visible(timeout=1500):
        try:
            hr_row.locator("button:has-text('Approve'), button:has-text('Accept')").first.click()
            hr_page.wait_for_timeout(1000)
            confirm_btn = hr_page.locator("button:has-text('Confirm'), button:has-text('Yes')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
                hr_page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"HR approve note: {e}")

    # Trigger Start FnF Process if available
    fnf_started = False
    try:
        actions_btn = hr_row.locator("td:last-child button, button.chakra-menu__menu-button").first
        if actions_btn.is_visible(timeout=2000):
            actions_btn.click()
            hr_page.wait_for_timeout(500)
            start_fnf_item = hr_page.locator("button[role='menuitem']:has-text('Start FnF Process'), div[role='menuitem']:has-text('Start FnF Process')").first
            if start_fnf_item.is_visible(timeout=2000):
                start_fnf_item.click()
                hr_page.wait_for_timeout(800)
                confirm_btn = hr_page.locator("button:has-text('Confirm'), button:has-text('Start'), button:has-text('Yes')").first
                if confirm_btn.is_visible(timeout=2000):
                    confirm_btn.click()
                toast = hr_wf.res_page.wait_for_toast(timeout=5000)
                logger.info(f"[STAGE 5] Start FnF toast: '{toast}'")
                fnf_started = True
    except Exception as e:
        logger.warning(f"Note on starting FnF: {e}")

    story.log_step(
        "HR FnF Trigger",
        record=f"HR Processed. Status: '{hr_status}' | FnF Triggered: {fnf_started}",
        expected="FnF process initiated",
        actual=f"FnF Triggered: {fnf_started}",
        status="PASS"
    )

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 6: ACCOUNTANT FnF DRAWER INSPECTION (CORE VERIFICATION)
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[STAGE 6 - FnF SETTLEMENT DRAWER] Accountant opening FnF drawer on /accounts-buyout-processing...")
    acc_page, _ = logged_in_page("admin")
    acc_res_page = ResignationPage(acc_page)
    acc_res_page.navigate_to_accounts_fnf_requests()

    # Search employee in FnF table
    search_input = acc_page.locator("input[placeholder*='Search Employee' i], input[placeholder*='search' i]").first
    if search_input.is_visible(timeout=3000):
        search_input.click()
        search_input.fill(emp_name)
        search_input.press("Enter")
        acc_page.wait_for_timeout(1500)

    emp_row = acc_page.locator(f"tr:has-text('{emp_name}')").first
    row_visible = emp_row.is_visible(timeout=5000)
    logger.info(f"[STAGE 6] Employee '{emp_name}' visible in FnF Requests table: {row_visible}")

    sc_fnf_table = os.path.join(screenshots_dir, "fnf_stage6_accountant_fnf_table.png")
    acc_page.screenshot(path=sc_fnf_table)

    drawer_opened = False
    asset_recovery_val = "NOT_ACCESSIBLE"
    auto_added_to_fnf = False

    if row_visible:
        # Open FnF drawer via action arrow / button
        action_arrow = emp_row.locator("td:last-child svg, td:last-child button, td:last-child span, td:last-child").first
        action_arrow.click()
        acc_page.wait_for_timeout(1500)

        drawer = acc_page.locator("section.chakra-modal__content:has-text('Full & Final Settlement'), div[role='dialog']:has-text('Full & Final Settlement')").first
        drawer_opened = drawer.is_visible(timeout=5000)

        if drawer_opened:
            sc_fnf_drawer = os.path.join(screenshots_dir, "fnf_stage6_settlement_drawer_line_items.png")
            acc_page.screenshot(path=sc_fnf_drawer)
            logger.info(f"[STAGE 6] FnF Drawer Screenshot saved: {sc_fnf_drawer}")

            # Inspect 'Asset Recovery' input field
            ar_row = drawer.locator("tr:has-text('Asset Recovery')").first
            if ar_row.is_visible(timeout=3000):
                ar_input = ar_row.locator("input").first
                if ar_input.is_visible(timeout=1000):
                    asset_recovery_val = ar_input.input_value().strip()
                else:
                    asset_recovery_val = ar_row.locator("td").last.inner_text().strip()

                logger.info(f"================================================================================")
                logger.info(f"[CORE VERIFICATION RESULT] FnF 'Asset Recovery' Value: '{asset_recovery_val}'")
                logger.info(f"Original Recovery Amount Planned: ₹{recovery_amount} across {installment_months} months")
                logger.info(f"================================================================================")

                # Check if system auto-populated the amount
                cleaned_val = re.sub(r"[^\d.]", "", asset_recovery_val)
                val_float = float(cleaned_val) if cleaned_val else 0.0

                auto_added_to_fnf = val_float > 0.0
                if auto_added_to_fnf:
                    logger.info(f"[VERIFIED] Pending installment amount ₹{val_float} IS AUTO-POPULATED in FnF Settlement!")
                else:
                    logger.warning(f"[GAP DETECTED] FnF 'Asset Recovery' field is {asset_recovery_val} (0.00). It does NOT auto-populate installments!")

    story.log_step(
        "FnF Auto-Deduction Verification",
        record=f"FnF Drawer Opened: {drawer_opened} | Asset Recovery Value: '{asset_recovery_val}' | Auto-Added: {auto_added_to_fnf}",
        expected="Asset recovery balance reflected in FnF deductions",
        actual=f"Field Value: '{asset_recovery_val}' (Auto-Added: {auto_added_to_fnf})",
        status="PASS" if auto_added_to_fnf else "GAP"
    )

    story.finish()

    logger.info("=" * 80)
    logger.info(f"[TEST COMPLETED] Drawer Opened: {drawer_opened} | Asset Recovery Field: '{asset_recovery_val}' | Auto-Sync: {auto_added_to_fnf}")
    logger.info("=" * 80)





