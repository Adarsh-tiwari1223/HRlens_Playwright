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

    def return_asset(self, asset_code_or_name: str, condition: str = "Good", return_date: str = None, remarks: str = None):
        """
        Returns an assigned asset and evaluates its condition (Good, Damaged, Repair Required, Lost).
        """
        logger.info(f"Returning asset: {asset_code_or_name} with Condition: {condition}")
        
        # 1. Search for the asset first to narrow down the list
        search_input = self.page.locator("input[placeholder*='Search']").first
        if search_input.is_visible():
            search_input.fill(asset_code_or_name)
            self.page.wait_for_timeout(2000)
            
        # 2. Locate row containing the asset code or name via text filtering
        row_locator = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
        row_locator.wait_for(state="visible", timeout=10000)
        
        # Check if there is an action button in the row or checkbox
        row_return_btn = row_locator.get_by_role("button", name=re.compile(r"(Return|Process Return|Receive)", re.I)).first
        if row_return_btn.is_visible():
            row_return_btn.click()
        else:
            # 3. Click the checkbox inside the matching row to select it
            checkbox = row_locator.locator("input[type='checkbox'], span.chakra-checkbox").first
            if checkbox.is_visible():
                checkbox.click()
                self.page.wait_for_timeout(500)
            
            # Click Bulk Return button (which should now be enabled)
            bulk_btn = self.page.locator(self.BULK_RETURN_BTN).first
            if bulk_btn.is_visible(timeout=2000):
                bulk_btn.click()
        
        # 4. Handle confirmation / condition dialog popup
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if dialog.is_visible(timeout=5000):
            # Return Date
            if return_date:
                try:
                    date_input = dialog.locator("input[type='date']").first
                    if date_input.is_visible():
                        date_input.fill(return_date)
                except Exception:
                    pass
            
            # Asset Condition evaluation (Good, Damaged, Repair Required, Lost)
            try:
                cond_select = dialog.get_by_label("Condition", exact=False).first
                if not cond_select.is_visible(timeout=500):
                    cond_select = dialog.locator("select").filter(has_text=re.compile(r"(Good|Damaged|Repair|Lost)", re.I)).first
                if cond_select.is_visible(timeout=500):
                    cond_select.select_option(label=condition)
            except Exception:
                try:
                    # Check radio or button options
                    dialog.get_by_text(condition, exact=True).first.click()
                except Exception:
                    pass

            # Remarks
            if remarks:
                try:
                    remarks_input = dialog.locator("textarea, input[placeholder*='Remarks' i], input[placeholder*='Notes' i]").first
                    if remarks_input.is_visible():
                        remarks_input.fill(remarks)
                except Exception:
                    pass

            # Click the proceed/return confirmation button
            confirm_btn = dialog.locator(self.CONFIRM_RETURN_BTN)
            if not confirm_btn.is_visible():
                confirm_btn = dialog.get_by_role("button", name=re.compile(r"(Return|Confirm|Yes|Proceed|Submit)", re.IGNORECASE)).first
            confirm_btn.click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
