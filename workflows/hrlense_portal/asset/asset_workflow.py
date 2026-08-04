"""
Asset Management Workflow Layer for HR Lens Portal.

Encapsulates reusable business workflows for Category management, Sub-Category setup,
Vendor registration, Asset procurement, assignment, maintenance, and returns.
"""

import logging
from playwright.sync_api import Page, expect
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage

logger = logging.getLogger(__name__)

class AssetWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.asset_master_page = AssetMasterPage(page)
        self.asset_procurement_page = AssetProcurementPage(page)
        self.asset_assignment_page = AssetAssignmentPage(page)
        self.asset_return_page = AssetReturnPage(page)

    def create_category_workflow(self, name: str, description: str = "", toggle_spans: bool = True) -> str:
        """Workflow to open Asset Master, add a category, fill details, and submit."""
        logger.info(f"[WORKFLOW] Creating Asset Category: '{name}'")
        self.asset_master_page.navigate_to_asset_master()
        self.asset_master_page.click_add_category()
        self.asset_master_page.fill_category_details(name=name, description=description, toggle_spans=toggle_spans)
        self.asset_master_page.click_create()
        toast = self.asset_master_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Category creation toast result: '{toast}'")
        return toast

    def update_category_workflow(self, existing_name: str, new_description: str) -> str:
        """Workflow to edit an existing category and update details."""
        logger.info(f"[WORKFLOW] Updating Asset Category: '{existing_name}'")
        self.asset_master_page.navigate_to_asset_master()
        self.asset_master_page.edit_category(existing_name)
        self.asset_master_page.fill_category_details(name=None, description=new_description, toggle_spans=False)
        self.asset_master_page.click_update()
        toast = self.asset_master_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Category update toast result: '{toast}'")
        return toast

    def create_sub_category_workflow(self, category_name: str, sub_category_name: str, prefix: str = "SUB", description: str = "") -> str:
        """Workflow to add a sub-category under a parent category."""
        logger.info(f"[WORKFLOW] Creating Sub-Category: '{sub_category_name}' under Category '{category_name}'")
        self.asset_master_page.navigate_to_asset_master()
        self.asset_master_page.navigate_to_sub_categories()
        self.asset_master_page.click_add_sub_category()
        self.asset_master_page.fill_sub_category_details(
            category_name=category_name,
            sub_category_name=sub_category_name,
            prefix=prefix,
            description=description,
            toggle_spans=True
        )
        self.asset_master_page.click_create()
        toast = self.asset_master_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Sub-Category creation toast result: '{toast}'")
        return toast

    def create_vendor_workflow(self, vendor_data: dict) -> str:
        """Workflow to create a new vendor under Asset Master."""
        logger.info(f"[WORKFLOW] Creating Vendor: '{vendor_data.get('name', 'N/A')}'")
        self.asset_master_page.navigate_to_asset_master()
        self.asset_master_page.navigate_to_vendors()
        self.asset_master_page.click_add_vendor()
        self.asset_master_page.fill_vendor_details(
            name=vendor_data.get("name"),
            contact_person=vendor_data.get("contact_person"),
            email=vendor_data.get("email"),
            phone=vendor_data.get("phone"),
            address=vendor_data.get("address"),
            gst=vendor_data.get("gst"),
            supports_amc=vendor_data.get("supports_amc", False),
            toggle_spans=vendor_data.get("toggle_spans", True)
        )
        self.asset_master_page.click_create()
        toast = self.asset_master_page.wait_for_toast_message()
        logger.info(f"[WORKFLOW] Vendor creation toast result: '{toast}'")
        return toast

    def asset_procurement_to_assignment_workflow(self, procurement_data: dict, assignment_data: dict):
        """Workflow executing end-to-end asset procurement followed by assignment."""
        logger.info("[WORKFLOW] Initiating asset procurement to assignment workflow")
        self.asset_procurement_page.create_procurement_request(procurement_data)
        self.asset_assignment_page.assign_asset_to_employee(assignment_data)
        logger.info("[WORKFLOW] Asset procurement and assignment completed")

    def ensure_single_category_with_subcategories_workflow(self, category_name: str = "Hardware", sub_categories: list[dict] = None) -> str:
        """
        Workflow ensuring a single parent Category record exists (e.g. 'Hardware')
        and attaching N sub-categories (Laptop, Desktop, Server, Monitor, etc.) underneath without duplicates.
        """
        logger.info(f"[WORKFLOW] Ensuring single Category record: '{category_name}' with N sub-categories.")
        cat_name = self.asset_master_page.ensure_category_exists(name=category_name)
        if sub_categories:
            for sub in sub_categories:
                sub_name = sub.get("name")
                prefix = sub.get("prefix", "SUB")
                self.asset_master_page.ensure_sub_category_exists(
                    category_name=cat_name,
                    sub_category_name=sub_name,
                    code_prefix=prefix
                )
        return cat_name
