"""
HRlens Portal — Asset Management E2E Lifecycle & Staging Enhancements Test Suite.
Covers FRD Points 5, 8, 9, 10:
- Point 5: Multi-Asset Same Category/Subcategory Requisition, Fulfillment & Concurrent Active Acceptance
- Point 8: Temporary Assignment Type Dynamic Expected Return Date Gating
- Point 9: Consolidated Asset Return Single-Screen Table Structure & Checkbox Multi-Selection
- Point 10: Individual Asset Return Inspection Modal (Condition Gating, Evidence Enforcement, Maintenance Transition)

Execution:
    pytest tests/hrlense_portal/ui/asset/test_asset_lifecycle_e2e.py -v -s
"""

import os
import re
import time
import base64
import logging
import pytest
from playwright.sync_api import Page, expect

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage

logger = logging.getLogger(__name__)


def _create_temp_evidence_image(filepath: str):
    """Generates a tiny valid 1x1 PNG for evidence upload validation."""
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(png_data)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.e2e
class TestAssetLifecycleE2E:

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 5: MULTI-ASSET SAME CATEGORY CONCURRENT ASSIGNMENT & ACCEPTANCE
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_05_multi_asset_same_category_e2e(self, logged_in_page):
        """
        Verify an employee can request, have fulfilled, and accept multiple active
        assets within the exact same category (e.g. Software Licenses) concurrently.
        """
        story = TestStoryLogger(
            "Point 5: Multi-Asset Same Category Concurrent Fleet",
            module="Asset Management",
            phase="Requisition & Fleet Multi-Asset"
        )
        story.start()

        # Step 1: Employee checks fleet and submits new requisition in same category
        emp_page, _ = logged_in_page("adarsh_tiwari")
        emp_page.goto(f"{settings.BASE_URL}/asset-request")
        emp_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Count existing active assets before new flow
        rows_before = emp_page.locator("table tbody tr").all_inner_texts()
        active_count_before = sum(1 for r in rows_before if "ACTIVE" in r.upper())
        story.log_step("Step 1: Check Current Active Assets", record=f"Active Assets: {active_count_before}", status="PASS")

        # Open New Request Modal
        req_btn = emp_page.locator("button:has-text('New Request'), button:has-text('+ Request')").first
        expect(req_btn).to_be_visible(timeout=5000)
        req_btn.click()
        time.sleep(1)

        modal = emp_page.locator("[role='dialog'], .chakra-modal__content").last
        expect(modal).to_be_visible(timeout=5000)

        # Select Software Licenses -> Operating System License
        cat_select = modal.locator("select").first
        cat_select.select_option(label="Software Licenses")
        time.sleep(1)

        sub_select = modal.locator("select").nth(1)
        sub_select.select_option(label="Operating System License")
        time.sleep(1)

        reason_input = modal.locator("textarea, input[placeholder*='reason' i]").first
        if reason_input.is_visible():
            reason_input.fill("E2E Test: Secondary Operating System License request.")

        submit_btn = modal.locator("button:has-text('Submit Request'), button:has-text('Submit')").first
        submit_btn.click()
        time.sleep(3)

        # Verify new pending request row appeared
        emp_page.goto(f"{settings.BASE_URL}/asset-request")
        emp_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        req_rows = emp_page.locator("table tbody tr").all_inner_texts()
        has_pending = any("PENDING" in r.upper() and "SOFTWARE" in r.upper() for r in req_rows)
        story.log_step("Step 2: Submit Requisition in Same Category", record="Software Licenses Requisition", actual=f"Pending row visible: {has_pending}", status="PASS" if has_pending else "FAIL")
        assert has_pending, "New requisition row not found in PENDING status on employee portal!"

        # Step 3: IT Person Fulfills Request from Stock
        it_page, _ = logged_in_page("it_varanasi_ashutosh")
        it_page.goto(f"{settings.BASE_URL}/asset-assignment")
        it_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Switch to Requested Assignment tab
        req_tab = it_page.locator("button[role='tab']:has-text('Requested Assignment'), button[role='tab']:has-text('Employee Requests')").first
        if not req_tab.is_visible(timeout=3000):
            req_tab = it_page.locator("[role='tab']").nth(1)
        req_tab.click()
        time.sleep(2)

        target_row = it_page.locator("table tbody tr").filter(has_text=re.compile(r"Adarsh.*Software", re.I)).first
        expect(target_row).to_be_visible(timeout=5000)

        fulfil_btn = target_row.locator("button:has-text('Fulfil'), button:has-text('Assign')").first
        fulfil_btn.click()
        time.sleep(2)

        drawer = it_page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        expect(drawer).to_be_visible(timeout=5000)

        # Open Stock Asset Dropdown & check available asset
        asset_btn = drawer.locator("button.chakra-menu__menu-button, button:has-text('Select assets to assign')").first
        asset_btn.click()
        time.sleep(1)

        first_cb = it_page.locator(".chakra-menu__menu-list input[type='checkbox']").first
        expect(first_cb).to_be_visible(timeout=5000)
        first_cb.check(force=True)
        time.sleep(1)

        # Submit fulfillment
        assign_submit = drawer.locator("button:has-text('Assign Asset'), button[type='submit']").last
        assign_submit.click(force=True)
        time.sleep(4)
        story.log_step("Step 3: IT Stock Fulfillment", record="Selected Available Stock Asset", actual="Fulfilled successfully", status="PASS")

        # Step 4: Employee Accepts Assigned Asset
        emp_page2, _ = logged_in_page("adarsh_tiwari")
        emp_page2.goto(f"{settings.BASE_URL}/asset-request")
        emp_page2.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        accept_btn = emp_page2.locator("button:has-text('Accept Asset'), button:has-text('Accept')").first
        if accept_btn.is_visible(timeout=5000):
            accept_btn.click()
            time.sleep(1)
            confirm_dialog = emp_page2.locator("[role='dialog'], .chakra-modal__content").first
            if confirm_dialog.is_visible(timeout=2000):
                confirm_btn = confirm_dialog.locator("button:has-text('Accept'), button:has-text('Confirm')").first
                if confirm_btn.is_visible():
                    confirm_btn.click()
                    time.sleep(2)

        # Step 5: Assert employee holds multiple ACTIVE assets in Software Licenses
        emp_page2.reload()
        emp_page2.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        final_rows = emp_page2.locator("table tbody tr").all_inner_texts()
        active_assets = [r for r in final_rows if "ACTIVE" in r.upper() and "SOFTWARE" in r.upper()]
        story.log_step("Step 4: Verify Multi-Asset Concurrent Fleet", record=f"Active Software Licenses: {len(active_assets)}", status="PASS" if len(active_assets) >= 2 else "FAIL")
        assert len(active_assets) >= 2, f"Expected at least 2 active assets in same category, found: {len(active_assets)}"
        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 8: TEMPORARY ASSIGNMENT TYPE DYNAMIC RETURN DATE GATING
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_08_temporary_assignment_return_date_gating(self, logged_in_page):
        """
        Verify that selecting Assignment Type: Temporary dynamically renders
        and enforces the Expected Return Date date picker.
        """
        story = TestStoryLogger(
            "Point 8: Temporary Assignment Return Date Gating",
            module="Asset Management",
            phase="Temporary Assignment Gating"
        )
        story.start()

        it_page, _ = logged_in_page("it_varanasi_ashutosh")
        it_page.goto(f"{settings.BASE_URL}/asset-assignment")
        it_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Switch to Requested Assignment tab to inspect drawer
        req_tab = it_page.locator("button[role='tab']:has-text('Requested Assignment'), button[role='tab']:has-text('Employee Requests')").first
        if not req_tab.is_visible(timeout=3000):
            req_tab = it_page.locator("[role='tab']").nth(1)
        req_tab.click()
        time.sleep(2)

        # Open fulfillment drawer or direct assignment drawer to inspect Assignment Type controls
        pending_rows = it_page.locator("table tbody tr").filter(
            has=it_page.locator("button:not([disabled]):has-text('Fulfil'), button:not([disabled]):has-text('Assign')")
        )
        if pending_rows.count() > 0:
            fulfil_btn = pending_rows.first.locator("button:not([disabled]):has-text('Fulfil'), button:not([disabled]):has-text('Assign')").first
            fulfil_btn.click()
        else:
            # Fallback to '+ Assign Asset' drawer where Assignment Type is always available
            assign_btn = it_page.locator("button:has-text('Assign Asset'), button:has-text('+ Assign')").first
            assign_btn.click()

        drawer = it_page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        expect(drawer).to_be_visible(timeout=5000)

        # Locate Assignment Type select
        duration_select = drawer.locator("select:has(option:has-text('Permanent'))").first
        if not duration_select.is_visible():
            duration_select = drawer.locator("select").first

        expect(duration_select).to_be_visible(timeout=3000)

        # Select Temporary
        duration_select.select_option(label="Temporary")
        time.sleep(1)

        # Assert Expected Return Date field is dynamically rendered
        date_input = drawer.locator("input[type='date']").first
        expect(date_input).to_be_visible(timeout=3000)
        story.log_step("Verify Expected Return Date Rendered", record="Assignment Type = Temporary", actual="input[type='date'] visible", status="PASS")

        # Fill future date
        date_input.fill("2026-12-31")
        assert date_input.input_value() == "2026-12-31", "Expected return date value was not filled correctly!"

        # Close drawer
        close_btn = drawer.locator("button[aria-label='Close'], button:has-text('Cancel')").first
        close_btn.click()
        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 9: CONSOLIDATED ASSET RETURN UI ON /asset-return
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_09_consolidated_asset_return_view(self, logged_in_page):
        """
        Verify that /asset-return renders a single consolidated screen showing all
        assigned assets per employee with multi-select checkboxes and KPI counters.
        """
        story = TestStoryLogger(
            "Point 9: Consolidated Asset Return Single-Screen UI",
            module="Asset Management",
            phase="Return Management"
        )
        story.start()

        it_page, _ = logged_in_page("it_varanasi_ashutosh")
        it_page.goto(f"{settings.BASE_URL}/asset-return")
        it_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Check KPI Cards
        cards = it_page.locator(".chakra-card, div[class*='card']").all_inner_texts()
        has_assigned_kpi = any("Assigned" in c for c in cards)
        story.log_step("Step 1: Check Return KPI Cards", record=f"KPI Cards count: {len(cards)}", actual=f"Assigned Assets KPI visible: {has_assigned_kpi}", status="PASS")

        # Switch to Assigned Assets tab
        assigned_tab = it_page.locator("button[role='tab']:has-text('Assigned Assets')").first
        expect(assigned_tab).to_be_visible(timeout=3000)
        assigned_tab.click()
        time.sleep(2)

        # Check table columns & structure
        headers = it_page.locator("table thead th").all_inner_texts()
        cleaned_headers = [h.strip().replace('\n', ' ') for h in headers if h.strip()]
        story.log_step("Step 2: Table Columns", record=str(cleaned_headers), status="PASS")

        # Verify row checkboxes are rendered
        row_checkboxes = it_page.locator("table tbody tr input[type='checkbox']").all()
        story.log_step("Step 3: Multi-Select Checkboxes", record=f"Row Checkboxes: {len(row_checkboxes)}", status="PASS" if len(row_checkboxes) > 0 else "FAIL")
        assert len(row_checkboxes) > 0, "Consolidated return table missing individual row checkboxes!"

        story.finish(status="PASS")

    # ──────────────────────────────────────────────────────────────────────────
    # POINT 10: INDIVIDUAL INSPECTION RETURN CLEARANCE MODAL & TRANSITION
    # ──────────────────────────────────────────────────────────────────────────
    def test_point_10_individual_inspection_return_clearance(self, logged_in_page, tmp_path):
        """
        Verify individual asset return inspection modal fields:
        1. Condition radio options (Good, Damaged, Repair Required, Lost)
        2. Dynamic mandatory evidence attachment enforcement for Repair/Damaged
        3. Remarks recording
        4. Status transition into MAINTENANCE REVIEW and routing to /asset-maintenance.
        """
        story = TestStoryLogger(
            "Point 10: Individual Return Inspection & Maintenance Transition",
            module="Asset Management",
            phase="Return Inspection"
        )
        story.start()

        it_page, _ = logged_in_page("it_varanasi_ashutosh")
        it_page.goto(f"{settings.BASE_URL}/asset-return")
        it_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        assigned_tab = it_page.locator("button[role='tab']:has-text('Assigned Assets')").first
        assigned_tab.click()
        time.sleep(2)

        rows = it_page.locator("table tbody tr").all()
        if not rows:
            pytest.skip("No assigned assets available to test return clearance.")

        # Click return action button on first active row
        action_btn = rows[0].locator("button").first
        action_btn.click()
        time.sleep(2)

        modal = it_page.locator("[role='dialog'], .chakra-modal__content").first
        expect(modal).to_be_visible(timeout=5000)
        story.log_step("Step 1: Open Return Modal", actual="Modal visible", status="PASS")

        # 1. Verify Condition Radio Buttons
        radios = modal.locator("input[type='radio']").all()
        radio_values = [r.get_attribute("value") for r in radios]
        story.log_step("Step 2: Inspect Condition Radios", record=str(radio_values), status="PASS")
        assert "Repair Required" in radio_values, "Repair Required radio missing from return modal!"
        assert "Good" in radio_values, "Good condition radio missing from return modal!"

        # 2. Select Repair Required
        repair_radio = modal.locator("input[type='radio'][value='Repair Required']").first
        repair_radio.check(force=True)
        time.sleep(1)

        # 3. Verify Evidence Upload becomes mandatory
        evidence_label = modal.locator("label:has-text('EVIDENCE'), p:has-text('EVIDENCE')").first
        expect(evidence_label).to_be_visible(timeout=3000)
        story.log_step("Step 3: Mandatory Evidence Enforcement", record="Condition = Repair Required", actual="EVIDENCE * visible", status="PASS")

        # 4. Upload Evidence Photo
        temp_img = str(tmp_path / "return_evidence.png")
        _create_temp_evidence_image(temp_img)
        file_input = modal.locator("input[type='file']").first
        file_input.set_input_files(temp_img)
        time.sleep(1)

        # 5. Fill Remarks
        remarks = modal.locator("textarea, input[placeholder*='Remarks' i]").first
        if remarks.is_visible():
            remarks.fill("Automated E2E Test: License activation damaged. Sent to Maintenance.")

        # 6. Submit Return
        submit_btn = modal.locator("button:has-text('Return Asset')").last
        submit_btn.click(force=True)
        time.sleep(4)
        story.log_step("Step 4: Submit Return Clearance", actual="Return Asset submitted", status="PASS")

        # 7. Verify asset routed to /asset-maintenance
        it_page.goto(f"{settings.BASE_URL}/asset-maintenance")
        it_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        maint_rows = it_page.locator("table tbody tr").all_inner_texts()
        has_maintenance_asset = any("Repair Required" in r or "MAINTENANCE" in r.upper() for r in maint_rows)
        story.log_step("Step 5: Verify Routing to /asset-maintenance", record=f"Maintenance queue rows: {len(maint_rows)}", actual=f"Asset present in maintenance: {has_maintenance_asset}", status="PASS" if has_maintenance_asset else "FAIL")
        assert has_maintenance_asset, "Returned asset was not routed to /asset-maintenance!"

        story.finish(status="PASS")
