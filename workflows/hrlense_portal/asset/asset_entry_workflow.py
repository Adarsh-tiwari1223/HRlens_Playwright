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
