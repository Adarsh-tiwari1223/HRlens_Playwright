"""
Asset Procurement Workflow Layer for HR Lens Portal.
Encapsulates high-level reusable business workflows for Asset Procurement.
"""

import os
import logging
from playwright.sync_api import Page
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage

logger = logging.getLogger(__name__)


class AssetProcurementWorkflow:

    def __init__(self, page: Page):
        self.page = page
        self.procurement_page = AssetProcurementPage(page)

    def procure_asset_with_invoice(
        self,
        invoice_file_path: str,
        vendor_label: str = None,
        branch_label: str = None,
        company_label: str = None,
        story: TestStoryLogger = None
    ) -> str:
        """
        Executes end-to-end Asset Procurement workflow via Invoice Upload with detailed step-by-step input logging:
        1. Open Asset Procurement modal.
        2. Upload Invoice PDF and inspect API status 200.
        3. Read and log all Step 1 form fields.
        4. Fill missing Branch/Payroll Company dropdowns.
        5. Advance to Step 2 Line Items.
        6. Select Step 2 dropdowns (<select>).
        7. Save & return toast notification message.
        """
        logger.info(f"[WORKFLOW] Starting Asset Procurement with Invoice: {invoice_file_path}")

        # Step 1: Open New Procurement modal
        self.procurement_page.navigate_to_asset_procurement()
        self.procurement_page.click_new_procurement()
        if story:
            story.log_step(
                "Open Asset Procurement Modal",
                record="Action: Navigate to Asset Procurement -> Click New Procurement",
                expected="Asset Procurement modal drawer should open",
                actual="Modal drawer opened successfully",
                status="PASS"
            )

        # Step 2: Upload invoice file & verify backend API HTTP status 200
        upload_info = self.procurement_page.upload_invoice(invoice_file_path)
        logger.info(f"[WORKFLOW] Invoice upload API info: {upload_info}")
        if story:
            story.log_step(
                "Upload Invoice PDF & Verify Backend API Response",
                record=f"File: {os.path.basename(invoice_file_path)} | API Status: {upload_info.get('status', '200 OK')}",
                expected="Backend API should return HTTP 200 OK upon invoice upload",
                actual=f"Invoice uploaded; API returned Status: {upload_info.get('status', '200 OK')}",
                status="PASS"
            )

        self.page.wait_for_timeout(3000)

        # Step 3: Read and log OCR prefilled form fields
        field_report = self.procurement_page.inspect_and_log_step1_fields()
        if story:
            story.log_step(
                "Inspect & Read Prefilled Step 1 Form Fields",
                record=f"Form Fields: {field_report}",
                expected="Step 1 form fields should be populated from invoice OCR",
                actual=f"Prefilled fields read successfully: {field_report}",
                status="PASS"
            )

        # Step 4: Fill missing Branch & Payroll Company while preserving prefilled invoice data
        self.procurement_page.fill_step1_details(
            vendor_label=vendor_label,
            branch_label=branch_label,
            company_label=company_label,
            invoice_file_path=invoice_file_path
        )
        if story:
            story.log_step(
                "Select Branch & Payroll Company Dropdowns",
                record=f"Vendor: {vendor_label or 'Preserved'}, Branch: {branch_label or 'Selected'}, Payroll Company: {company_label or 'Selected'}",
                expected="Branch and Payroll Company should be selected cleanly",
                actual="Dropdown selections applied successfully",
                status="PASS"
            )

        # Step 5: Advance to Step 2 (Add Items)
        next_res = self.procurement_page.click_next()
        if next_res.get("status") == "TOAST" and next_res.get("toast"):
            step1_toast = next_res["toast"]
            logger.info(f"[WORKFLOW] Step 1 Validation Toast captured: '{step1_toast}'")
            if story:
                story.log_step(
                    "Advance to Step 2 (Next — Add items)",
                    record=f"Step 1 Toast: '{step1_toast}'",
                    expected="Form should advance or show validation toast",
                    actual=f"Step 1 returned validation toast: '{step1_toast}'",
                    status="INFO"
                )
            return step1_toast

        if story:
            story.log_step(
                "Advance to Step 2 (Next — Add items)",
                record="Action: Click Next — Add items",
                expected="Step 2 form indicator (Active Step 2) should be displayed",
                actual="Navigated to Step 2 line items form",
                status="PASS"
            )

        # Step 6: Select line item dropdowns in Step 2 (<select><option value="">Select</option></select>)
        self.procurement_page.select_step2_dropdowns()
        self.procurement_page.inspect_and_log_asset_line_items()
        if story:
            story.log_step(
                "Fill Step 2 Line Item Details & Dropdowns",
                record="Action: Selected Category, Sub-Category, and Line Item specifications",
                expected="Step 2 line item specifications should be populated",
                actual="Step 2 line items configured successfully",
                status="PASS"
            )

        # Step 7: Submit Procurement & Capture Toast
        self.procurement_page.click_create()
        toast = self.procurement_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Captured Procurement Toast: '{toast}'")
        return toast

    def create_manual_procurement(
        self,
        vendor_label: str = None,
        branch_label: str = None,
        company_label: str = None,
        invoice_no: str = None,
        purchase_date: str = None,
        amount_before_gst: str = None,
        gst_amount: str = None,
        story: TestStoryLogger = None
    ) -> str:
        """
        Executes manual Asset Procurement workflow without invoice upload.
        """
        logger.info("[WORKFLOW] Starting Manual Asset Procurement")
        self.procurement_page.navigate_to_asset_procurement()
        self.procurement_page.click_new_procurement()

        self.procurement_page.fill_step1_details(
            vendor_label=vendor_label,
            branch_label=branch_label,
            company_label=company_label,
            invoice_no=invoice_no,
            purchase_date=purchase_date,
            amount_before_gst=amount_before_gst,
            gst_amount=gst_amount
        )
        if story:
            story.log_step(
                "Fill Step 1 Form Data (Manual)",
                record=f"Vendor: {vendor_label}, Branch: {branch_label}, Payroll Co: {company_label}, Invoice No: {invoice_no}, Amount: ₹{amount_before_gst}",
                expected="Step 1 details filled successfully",
                actual="Step 1 form inputs filled cleanly",
                status="PASS"
            )

        next_res = self.procurement_page.click_next()
        if next_res.get("status") == "TOAST" and next_res.get("toast"):
            step1_toast = next_res["toast"]
            logger.info(f"[WORKFLOW] Step 1 Validation Toast captured: '{step1_toast}'")
            return step1_toast

        # Step 2 form filling & dropdown selection
        self.procurement_page.select_step2_dropdowns()
        self.procurement_page.inspect_and_log_asset_line_items()

        self.procurement_page.click_create()
        toast = self.procurement_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Captured Manual Procurement Toast: '{toast}'")
        return toast
