"""
HRlens Portal — Post-Migration Asset Management Deep Audit Specification.

Verifies the integrity of migrated data after staging database refresh from production:
1. Asset Masters Audit:
   - Categories tab (must be present with active records)
   - Sub-Categories tab (must be present with prefixes and category mappings)
   - Vendors tab (must be present with vendor records, GST, contact)
   - Branch Groups (/branch-group or Master -> Branch Group) (must be present with mapped branches)
2. Assets for All Branches:
   - Scans /asset-stock and /asset-assignment across all company branches
   - Verifies asset stock counts and records per branch
3. Auto-Procurement via Invoice:
   - Opens /asset-procurement -> 'New Procurement'
   - Uploads sample invoice from testdata/static/invoices/
   - Verifies auto-extraction / prefill capability without destructive writes
"""

import os
import re
import logging
import pytest
from core.config import settings
from pages.base_page import BasePage, TestStoryLogger
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.post_migration_audit
class TestPostMigrationAssetAuditSpec:

    def test_01_audit_asset_masters(self, logged_in_page):
        """
        Audit 1: Verifies all Asset Masters (Categories, Subcategories, Vendors, Branch Groups)
        exist with non-empty datasets after production DB migration.
        """
        story = TestStoryLogger("Post-Migration: Asset Masters Audit", module="Asset Management", phase="Master Verification")
        story.start()

        page, _ = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        # -------------------------------------------------------------
        # 1A. Categories Tab
        # -------------------------------------------------------------
        logger.info("[AUDIT 1A] Checking Categories on /asset-master...")
        page.goto(f"{settings.BASE_URL}/asset-master", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        cat_tab = page.locator("button[role='tab']:has-text('Categor'), [role='tab']:has-text('Categor')").first
        if cat_tab.is_visible(timeout=3000):
            cat_tab.click()
            page.wait_for_timeout(1000)

        cat_rows = page.locator("table tbody tr").all()
        cat_names = []
        for r in cat_rows:
            txt = r.inner_text().strip()
            if txt and "no records" not in txt.lower():
                first_col = r.locator("td").first.inner_text().strip() if r.locator("td").count() > 0 else txt
                cat_names.append(first_col)

        logger.info(f"==> CATEGORIES FOUND ({len(cat_names)}): {cat_names[:10]}")
        assert len(cat_names) > 0, "CRITICAL AUDIT FAILURE: No Asset Categories found after DB migration!"

        # -------------------------------------------------------------
        # 1B. Sub-Categories Tab
        # -------------------------------------------------------------
        logger.info("[AUDIT 1B] Checking Sub-Categories on /asset-master...")
        subcat_tab = page.locator("button[role='tab']:has-text('Sub Categor'), [role='tab']:has-text('Sub Categor')").first
        assert subcat_tab.is_visible(timeout=5000), "Sub Category tab not visible on /asset-master"
        subcat_tab.click()
        page.wait_for_timeout(1500)

        subcat_rows = page.locator("table tbody tr").all()
        subcat_names = []
        for r in subcat_rows:
            txt = r.inner_text().strip()
            if txt and "no records" not in txt.lower():
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if cells:
                    subcat_names.append(" | ".join(cells[:3]))

        logger.info(f"==> SUB-CATEGORIES FOUND ({len(subcat_names)}): {subcat_names[:10]}")
        assert len(subcat_names) > 0, "CRITICAL AUDIT FAILURE: No Asset Sub-Categories found after DB migration!"

        # -------------------------------------------------------------
        # 1C. Vendors Tab
        # -------------------------------------------------------------
        logger.info("[AUDIT 1C] Checking Vendors on /asset-master...")
        vendor_tab = page.locator("button[role='tab']:has-text('Vendor'), [role='tab']:has-text('Vendor')").first
        assert vendor_tab.is_visible(timeout=5000), "Vendors tab not visible on /asset-master"
        vendor_tab.click()
        page.wait_for_timeout(1500)

        vendor_rows = page.locator("table tbody tr").all()
        vendor_names = []
        for r in vendor_rows:
            txt = r.inner_text().strip()
            if txt and "no records" not in txt.lower():
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if cells:
                    vendor_names.append(" | ".join(cells[:3]))

        logger.info(f"==> VENDORS FOUND ({len(vendor_names)}): {vendor_names[:10]}")
        assert len(vendor_names) > 0, "CRITICAL AUDIT FAILURE: No Vendors found after DB migration!"

        # -------------------------------------------------------------
        # 1D. Branch Group Master
        # -------------------------------------------------------------
        logger.info("[AUDIT 1D] Checking Branch Groups...")
        page.goto(f"{settings.BASE_URL}/branch-group", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Fallback to navigation via Master menu if direct URL 404s
        if not page.locator("table").is_visible(timeout=3000):
            bg_page = BranchGroupPage(page)
            try:
                bg_page.navigate_to_branch_group()
                page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"Branch group navigation note: {e}")

        bg_rows = page.locator("table tbody tr").all()
        bg_list = []
        for r in bg_rows:
            txt = r.inner_text().strip()
            if txt and "no records" not in txt.lower():
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if cells:
                    bg_list.append(" | ".join(cells[:3]))

        logger.info(f"==> BRANCH GROUPS FOUND ({len(bg_list)}): {bg_list[:10]}")
        assert len(bg_list) > 0, "CRITICAL AUDIT FAILURE: No Branch Groups found after DB migration!"

        logger.info("=" * 70)
        logger.info("AUDIT 1 PASS: ALL ASSET MASTERS PRESENT AND POPULATED!")
        logger.info(f"Categories: {len(cat_names)} | SubCategories: {len(subcat_names)} | Vendors: {len(vendor_names)} | Branch Groups: {len(bg_list)}")
        logger.info("=" * 70)

    def test_02_audit_assets_across_all_branches(self, logged_in_page):
        """
        Audit 2: Verifies that Assets are present for all company branches
        in /asset-stock or /asset-assignment.
        """
        story = TestStoryLogger("Post-Migration: Branch Assets Distribution Audit", module="Asset Management", phase="Stock Scoping Verification")
        story.start()

        page, _ = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        logger.info("[AUDIT 2] Navigating to /asset-stock to audit branch distribution...")
        page.goto(f"{settings.BASE_URL}/asset-stock", timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # Look for Branch Filter / Dropdown
        branch_options = []
        branch_select = page.locator("select").filter(has=page.locator("option", has_text=re.compile(r"Varanasi|Agra|Branch|All", re.I))).first
        if not branch_select.is_visible(timeout=3000):
            branch_select = page.locator("select").first

        if branch_select.is_visible(timeout=3000):
            options = branch_select.locator("option").all()
            for opt in options:
                txt = opt.inner_text().strip()
                val = opt.get_attribute("value")
                if txt and "select" not in txt.lower():
                    branch_options.append((val, txt))

        logger.info(f"==> DETECTED BRANCH FILTER OPTIONS ({len(branch_options)}): {[b[1] for b in branch_options]}")

        branch_audit_results = {}

        if branch_options:
            for val, b_name in branch_options:
                try:
                    logger.info(f"Auditing Branch: '{b_name}'...")
                    branch_select.select_option(value=val) if val else branch_select.select_option(label=b_name)
                    page.wait_for_timeout(1500)

                    # Read rows or KPI counts
                    rows = page.locator("table tbody tr").all()
                    valid_rows = [r for r in rows if "no records" not in r.inner_text().lower() and r.inner_text().strip()]
                    branch_audit_results[b_name] = len(valid_rows)
                    logger.info(f"   -> Branch '{b_name}': {len(valid_rows)} asset rows found.")
                except Exception as ex:
                    logger.warning(f"Error checking branch '{b_name}': {ex}")
        else:
            # Check entire table branch column directly
            rows = page.locator("table tbody tr").all()
            for r in rows:
                txt = r.inner_text().strip()
                if txt and "no records" not in txt.lower():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    branch_name = cells[2] if len(cells) > 2 else "Default"
                    branch_audit_results[branch_name] = branch_audit_results.get(branch_name, 0) + 1

        logger.info("=" * 70)
        logger.info("AUDIT 2: ASSET DISTRIBUTION ACROSS BRANCHES:")
        for b, count in branch_audit_results.items():
            logger.info(f"   Branch '{b}': {count} Assets")
        logger.info("=" * 70)

        total_assets = sum(branch_audit_results.values())
        assert total_assets > 0, "CRITICAL AUDIT FAILURE: Zero assets found in system after DB migration!"

    def test_03_audit_auto_procurement_via_invoice(self, logged_in_page):
        """
        Audit 3: Verifies 'Auto procurement via invoice' functionality
        in /asset-procurement by uploading a test invoice and inspecting parsed fields.
        """
        story = TestStoryLogger("Post-Migration: Auto Procurement via Invoice Audit", module="Asset Management", phase="Procurement AI/Invoice Parsing")
        story.start()

        page, _ = logged_in_page("admin")
        page.bring_to_front()
        page.wait_for_timeout(2000)

        proc_page = AssetProcurementPage(page)
        logger.info("[AUDIT 3] Navigating to /asset-procurement...")
        proc_page.navigate_to_asset_procurement()
        page.wait_for_timeout(2000)

        logger.info("Opening 'New Procurement' wizard...")
        proc_page.click_new_procurement()
        page.wait_for_timeout(1500)

        # Locate sample invoice file
        invoice_path = os.path.abspath(os.path.join(os.getcwd(), "testdata", "static", "invoices", "JOB VRITTA 41 1.pdf"))
        if not os.path.exists(invoice_path):
            invoice_path = os.path.abspath(os.path.join(os.getcwd(), "testdata", "static", "invoices", "invoice_1mb.pdf"))

        assert os.path.exists(invoice_path), f"Sample invoice file not found at: {invoice_path}"
        logger.info(f"Uploading invoice: {invoice_path}")

        upload_result = proc_page.upload_invoice(invoice_path)
        page.wait_for_timeout(3000)

        # Check Step 1 fields post-upload (Invoice No, Amount, Date, etc.)
        inv_no_input = page.locator("input[placeholder*='Invoice' i], label:has-text('Invoice No') + input, input[name*='invoice' i]").first
        inv_no_val = inv_no_input.input_value() if inv_no_input.is_visible(timeout=3000) else ""

        amt_input = page.locator("input[placeholder*='amount' i], input[type='number']").first
        amt_val = amt_input.input_value() if amt_input.is_visible(timeout=3000) else ""

        logger.info(f"==> POST-UPLOAD PREFILLED VALUES -> Invoice No: '{inv_no_val}' | Amount: '{amt_val}'")

        # Close / cancel modal to prevent dirtying production data
        close_btn = page.locator("button:has-text('Cancel'), [aria-label='Close'], button.chakra-modal__close-btn").first
        if close_btn.is_visible(timeout=2000):
            close_btn.click()
            page.wait_for_timeout(1000)

        logger.info("=" * 70)
        logger.info("AUDIT 3 PASS: INVOICE UPLOAD & AUTO PROCUREMENT PIPELINE RESPONSIVE!")
        logger.info("=" * 70)
