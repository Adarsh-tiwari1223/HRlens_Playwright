import logging
import re
from pages.base_page import BasePage

from core.config import settings
logger = logging.getLogger(__name__)

class AssetRequestPage(BasePage):
    ASSET_REQUEST_LINK = "role=link[name='• Asset Request']"
    RETURN_BTN = "role=button[name='Return']" # Or whatever return request button is
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_request(self):
        logger.info("Navigating to Asset Request page directly")
        self.page.goto(f"{settings.BASE_URL}/asset-request")
        self.page.wait_for_load_state("domcontentloaded")

    def accept_asset(self, asset_code_or_name: str) -> bool:
        logger.info(f"Accepting asset: {asset_code_or_name}")
        self.page.wait_for_timeout(2000)
        # Target the card container class '.css-prwjms' containing the asset code
        card_locator = self.page.locator(".css-prwjms").filter(has_text=asset_code_or_name).first
        accept_btn = card_locator.get_by_role("button", name="Accept Asset")
        if accept_btn.is_visible():
            accept_btn.click()
            return True
        logger.warning(f"Accept Asset button not visible for asset: {asset_code_or_name}")
        return False

    def create_new_request(self, reason: str, remarks: str = None) -> bool:
        logger.info("Creating new asset request via form")
        self.page.get_by_role("button", name="New Request").click()
        
        dialog = self.page.locator("[role='dialog'][aria-modal='true']")
        dialog.wait_for(state="visible", timeout=10000)
        
        # Select first category and subcategory from form dropdowns
        category_select = dialog.get_by_label("Category*", exact=True)
        category_select.wait_for(state="visible")
        category_select.select_option(index=1)
        self.page.wait_for_timeout(1000)
        
        sub_select = dialog.get_by_label("Sub Category*", exact=True)
        sub_select.wait_for(state="visible")
        sub_select.select_option(index=1)
        self.page.wait_for_timeout(1000)
        
        # Reason
        dialog.get_by_placeholder(re.compile(r"^e\.g\. My current laptop is too")).fill(reason)
        
        # Remarks
        if remarks:
            remarks_input = dialog.get_by_placeholder(re.compile(r"^Any additional remarks", re.IGNORECASE))
            if remarks_input.is_visible():
                remarks_input.fill(remarks)
            
        # Submit
        dialog.get_by_role("button", name="Submit Request").click()
        self.page.wait_for_timeout(2000)
        return True

    def request_return(self, asset_code_or_name: str) -> bool:
        logger.info(f"Handling return request for asset: {asset_code_or_name}")
        self.page.wait_for_timeout(2000)
        # Target the card container class '.css-prwjms' containing the asset code
        card_locator = self.page.locator(".css-prwjms").filter(has_text=asset_code_or_name).first
        return_btn = card_locator.get_by_role("button", name=re.compile(r"(Return|Request Return)", re.IGNORECASE))
        if not return_btn.is_visible():
            return_btn = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).get_by_role("button", name=re.compile(r"(Return|Request Return)", re.IGNORECASE))
            
        if return_btn.is_visible():
            logger.info("Clicking Return/Request Return button.")
            return_btn.click()
            self.page.wait_for_timeout(1000)
            
            modal = self.page.locator("[role='dialog'][aria-modal='true']")
            if modal.is_visible():
                confirm_btn = modal.get_by_role("button", name=re.compile(r"(Return|Confirm|Yes|Proceed)", re.IGNORECASE))
                confirm_btn.click()
                self.page.wait_for_timeout(1000)
            return True
            
        logger.warning(f"Return button not found or visible for asset: {asset_code_or_name}")
        return False

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
