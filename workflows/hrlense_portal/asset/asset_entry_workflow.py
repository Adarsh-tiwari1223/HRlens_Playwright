"""
Asset Entry Workflow Layer for HR Lens Portal.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage

logger = logging.getLogger(__name__)


class AssetEntryWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.entry_page = AssetEntryPage(page)

    def generate_assets_workflow(self, procurement_code: str = None) -> dict:
        """Executes the Generate Assets workflow via procurement selection."""
        logger.info("[WORKFLOW] Executing Generate Assets workflow")
        self.entry_page.navigate_to_asset_entry()
        self.entry_page.click_generate_assets_button()
        form_data = self.entry_page.fill_generate_assets_form(procurement_code=procurement_code)
        toast = self.entry_page.click_generate_assets_submit()
        return {"form_data": form_data, "toast": toast}

    def register_new_asset_workflow(self, asset_data: dict) -> dict:
        """Executes the complete manual asset creation workflow."""
        logger.info(f"[WORKFLOW] Registering manual asset: {asset_data.get('name') or asset_data.get('asset_name', 'N/A')}")
        self.entry_page.navigate_to_asset_entry()
        self.entry_page.click_add_asset()
        
        # Unpack dict if passed as dict
        data = dict(asset_data)
        if "asset_name" in data and "name" not in data:
            data["name"] = data.pop("asset_name")
            
        filled = self.entry_page.fill_asset_details(**data)
        toast = self.entry_page.click_save_and_generate_qr()
        return {
            "data": filled,
            "toast": toast
        }

    def verify_asset_edit_prefilled_workflow(self, asset_identifier: str = None) -> dict:
        """
        Navigates to /asset-entry, locates target asset, clicks Edit,
        reads all prefilled form fields, closes modal, and returns verification summary.
        """
        logger.info(f"[WORKFLOW] Verifying prefilled data for asset edit: '{asset_identifier or 'First visible asset'}'")
        self.entry_page.navigate_to_asset_entry()
        row_info = self.entry_page.click_edit_asset(asset_identifier)
        prefilled_data = self.entry_page.get_prefilled_asset_data()
        self.entry_page.close_edit_modal()
        return {
            "row_info": row_info,
            "prefilled_data": prefilled_data
        }

