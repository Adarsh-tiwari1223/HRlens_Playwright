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

    def register_new_asset_workflow(self, asset_data: dict):
        logger.info(f"[WORKFLOW] Registering asset: {asset_data.get('asset_name', 'N/A')}")
        self.entry_page.navigate_to_asset_entry()
        self.entry_page.fill_asset_details(asset_data)
        self.entry_page.save_asset()
