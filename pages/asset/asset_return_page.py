import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetReturnPage(BasePage):
    BULK_RETURN_BTN = "role=button[name='Bulk Return']"
    CONFIRM_RETURN_BTN = "role=button[name='Return Asset']" # Confirmation modal button
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_return(self):
        logger.info("Navigating to Asset Return page")
        self.page.goto(f"{settings.BASE_URL}/asset-return")
        self.page.wait_for_load_state("domcontentloaded")

    def return_asset(self, asset_code_or_name: str):
        logger.info(f"Returning asset: {asset_code_or_name}")
        
        # 1. Search for the asset first to narrow down the list
        search_input = self.page.locator("input[placeholder*='Search']").first
        if search_input.is_visible():
            search_input.fill(asset_code_or_name)
            self.page.wait_for_timeout(2000)
            
        # 2. Locate row containing the asset code or name via text filtering
        row_locator = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
        row_locator.wait_for(state="visible", timeout=10000)
        
        # 3. Click the checkbox inside the matching row to select it
        checkbox = row_locator.locator("input[type='checkbox'], span.chakra-checkbox").first
        checkbox.wait_for(state="visible")
        checkbox.click()
        self.page.wait_for_timeout(500)
        
        # 3. Click Bulk Return button (which should now be enabled)
        self.page.locator(self.BULK_RETURN_BTN).wait_for(state="visible", timeout=5000)
        self.click(self.BULK_RETURN_BTN)
        
        # 4. Confirm in the dialog popup
        self.page.locator("[role='dialog'][aria-modal='true']").wait_for(state="visible", timeout=5000)
        
        # Click the proceed/return confirmation button
        # Usually labeled "Return Asset" or similar
        confirm_btn = self.page.locator("[role='dialog'][aria-modal='true']").locator(self.CONFIRM_RETURN_BTN)
        if not confirm_btn.is_visible():
            confirm_btn = self.page.locator("[role='dialog'][aria-modal='true']").get_by_role("button", name=re.compile(r"(Return|Confirm|Yes|Proceed)", re.IGNORECASE))
        confirm_btn.click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
