"""
Asset Master Workflow Layer for HR Lens Portal.
Encapsulates category, subcategory, and vendor creation workflows.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage

logger = logging.getLogger(__name__)

class AssetMasterWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.asset_master_page = AssetMasterPage(page)

    def create_category_workflow(self, name: str, description: str = "", toggle_spans: bool = False) -> str:
        self.asset_master_page.navigate_to_asset_master()
        self.asset_master_page.click_add_category()
        self.asset_master_page.fill_category_details(name=name, description=description, toggle_spans=toggle_spans)
        self.asset_master_page.click_create()
        return self.asset_master_page.wait_for_toast_message()

    def create_vendor_workflow(self, vendor_data: dict) -> str:
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
        return self.asset_master_page.wait_for_toast_message()

    def setup_category_with_subcategories_workflow(self) -> tuple[str, list[dict]]:
        """
        Flowchart Implementation:
        Open Asset Master -> Open Sub-Category Tab -> Check existing Sub-Category records.
        ├── Sub-Category records exist: Go to Category Tab -> Create NEW Category -> Go to Sub-Category Tab -> Create 2-3 Sub-Categories -> Verify -> PASS
        └── No Sub-Category records: Create Category -> Create 2-3 Sub-Categories -> Verify relationship -> PASS
        """
        logger.info("Executing Flowchart Category-SubCategory Setup & Verification Workflow...")
        return self.asset_master_page.ensure_category_with_sub_categories_decision_tree()
