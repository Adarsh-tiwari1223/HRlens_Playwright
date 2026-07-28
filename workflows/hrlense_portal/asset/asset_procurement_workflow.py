"""
Asset Procurement Workflow Layer for HR Lens Portal.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.asset.asset_procurement_page import AssetProcurementPage

logger = logging.getLogger(__name__)

class AssetProcurementWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.procurement_page = AssetProcurementPage(page)

    def create_procurement_workflow(self, procurement_data: dict):
        logger.info("[WORKFLOW] Submitting asset procurement request")
        self.procurement_page.create_procurement_request(procurement_data)
