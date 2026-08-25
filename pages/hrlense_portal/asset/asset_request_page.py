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

    def accept_asset(self, asset_code_or_name: str = None) -> bool:
        """Accepts an assigned asset on the employee portal."""
        logger.info(f"Accepting asset: {asset_code_or_name or 'First Pending Asset'}")
        self.page.wait_for_timeout(1000)
        accept_btn = None
        if asset_code_or_name:
            card_locator = self.page.locator(".css-prwjms, .chakra-card, div.chakra-stack, table tbody tr, div[role='row']").filter(has_text=asset_code_or_name).first
            accept_btn = card_locator.get_by_role("button", name=re.compile(r"Accept Asset|Accept", re.I)).first
        
        if not accept_btn or not accept_btn.is_visible(timeout=2000):
            accept_btn = self.page.get_by_role("button", name=re.compile(r"Accept Asset|Accept", re.I)).first

        if accept_btn.is_visible(timeout=3000):
            accept_btn.click()
            self.page.wait_for_timeout(500)

            # Check if confirmation modal dialog opens
            dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
            if dialog.is_visible(timeout=2000):
                confirm_btn = dialog.get_by_role("button", name=re.compile(r"(Accept|Confirm|Yes|Proceed)", re.I)).first
                if confirm_btn.is_visible(timeout=1000):
                    confirm_btn.click()
                    self.page.wait_for_timeout(500)

            # Wait for any spinner to disappear
            try:
                self.page.locator(".chakra-spinner, span:has-text('Loading')").wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
            return True
        logger.warning(f"Accept Asset button not visible for asset: {asset_code_or_name or 'any asset'}")
        return False

    def reject_asset(self, asset_code_or_name: str = None, reason: str = None, rejection_reason: str = None, **kwargs) -> bool:
        """
        Rejects an assigned asset with reason modal and spinner wait:
        1. Clicks 'Reject' button.
        2. Fills 'Reason for Rejection' textarea (5-500 chars).
        3. Clicks 'Submit Rejection'.
        4. Waits for spinner completion.
        """
        fill_reason = rejection_reason or reason or "Received the wrong specification, already have a similar device."
        logger.info(f"Rejecting asset: {asset_code_or_name or 'First Pending Asset'} with reason: '{fill_reason}'")
        self.page.wait_for_timeout(1000)
        reject_btn = None
        if asset_code_or_name:
            card_locator = self.page.locator(".css-prwjms, .chakra-card, div.chakra-stack, table tbody tr, div[role='row']").filter(has_text=asset_code_or_name).first
            reject_btn = card_locator.locator("button:has-text('Reject')").first
        
        if not reject_btn or not reject_btn.is_visible(timeout=2000):
            reject_btn = self.page.locator("button:has-text('Reject')").first

        if reject_btn.is_visible(timeout=3000):
            reject_btn.click()
            self.page.wait_for_timeout(500)

            # Locate Reject Assignment modal dialog
            dialog = self.page.locator("[role='dialog'], .chakra-modal__content").filter(has_text=re.compile(r"Reject Assignment|Reason for Rejection", re.I)).first
            if not dialog.is_visible(timeout=2000):
                dialog = self.page.locator("[role='dialog'], .chakra-modal__content").first

            if dialog.is_visible(timeout=2000):
                reason_input = dialog.locator("textarea, input[placeholder*='wrong specification' i], input[placeholder*='reason' i]").first
                if reason_input.is_visible(timeout=1000):
                    reason_input.fill(fill_reason)
                    self.page.wait_for_timeout(300)

                submit_btn = dialog.locator("button:has-text('Submit Rejection'), button:has-text('Reject')").first
                if submit_btn.is_visible(timeout=1000):
                    submit_btn.click()
                    self.page.wait_for_timeout(500)

            # Wait for any spinner to disappear
            try:
                self.page.locator(".chakra-spinner, span:has-text('Loading')").wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
            return True
        logger.warning(f"Reject Asset button not visible for asset: {asset_code_or_name or 'any asset'}")
        return False

    def search_assigned_asset(self, asset_code_or_name: str) -> dict:
        """
        Searches assigned assets table using the search box:
        <input placeholder="Search assigned assets…" class="chakra-input css-bdhhlu" value="">
        Returns the row data and status.
        """
        search_input = self.page.locator("input[placeholder*='Search assigned assets' i]").first
        if search_input.is_visible(timeout=2000):
            search_input.fill(asset_code_or_name)
            self.page.wait_for_timeout(800)

        try:
            self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=3000)
        except Exception:
            pass

        row_texts = [r.strip() for r in self.page.locator("table tbody tr").all_inner_texts() if r.strip()]
        if not row_texts:
            return {"found": False, "status": "EMPTY", "row_text": ""}

        matching_text = ""
        for rt in row_texts:
            if asset_code_or_name.lower() in rt.lower():
                matching_text = rt
                break
        if not matching_text and row_texts:
            matching_text = row_texts[0]

        status = "UNKNOWN"
        for candidate in ["ACTIVE", "REJECTED", "PENDING", "RETURNED", "ASSIGNED"]:
            if candidate in matching_text.upper():
                status = candidate
                break

        return {
            "found": True,
            "status": status,
            "row_text": matching_text
        }

    def create_new_request(self, reason: str = "Required for project development.", remarks: str = None, category: str = None, sub_category: str = None) -> dict:
        logger.info(f"Creating new asset request: Category='{category or 'Default'}', SubCategory='{sub_category or 'Default'}'")
        new_req_btn = self.page.get_by_role("button", name=re.compile(r"New Request|\+ Request", re.I)).first
        if not new_req_btn.is_visible(timeout=3000):
            new_req_btn = self.page.locator("button:has-text('Request')").first
        new_req_btn.click()
        
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").last
        dialog.wait_for(state="visible", timeout=5000)
        
        # Select Category
        category_select = dialog.get_by_label("Category*", exact=True)
        if not category_select.is_visible(timeout=1000):
            category_select = dialog.locator("select").first
        category_select.wait_for(state="visible", timeout=2000)
        
        selected_cat = ""
        if category:
            try:
                category_select.select_option(label=category)
                selected_cat = category
            except Exception:
                category_select.select_option(index=1)
        else:
            category_select.select_option(index=1)
        self.page.wait_for_timeout(800)
        
        # Select Sub Category
        sub_select = dialog.get_by_label("Sub Category*", exact=False)
        if not sub_select.is_visible(timeout=1000):
            sub_select = dialog.locator("select").nth(1)
        sub_select.wait_for(state="visible", timeout=3000)
        
        selected_sub = ""
        try:
            sub_select.locator("option:not([value=''])").first.wait_for(state="attached", timeout=3000)
            if sub_category:
                try:
                    sub_select.select_option(label=sub_category)
                    selected_sub = sub_category
                except Exception:
                    sub_select.select_option(index=1)
            else:
                sub_select.select_option(index=1)
        except Exception:
            try:
                sub_select.select_option(index=0)
            except Exception:
                pass
        self.page.wait_for_timeout(800)
        
        # Reason
        reason_input = dialog.get_by_placeholder(re.compile(r"^e\.g\. My current laptop is too|Reason", re.I)).first
        if not reason_input.is_visible(timeout=1000):
            reason_input = dialog.locator("textarea, input[placeholder*='reason' i]").first
        if reason_input.is_visible(timeout=1000):
            reason_input.fill(reason)
        
        # Remarks
        if remarks:
            remarks_input = dialog.get_by_placeholder(re.compile(r"^Any additional remarks|Remarks", re.I)).first
            if remarks_input.is_visible(timeout=1000):
                remarks_input.fill(remarks)
            
        # Submit
        submit_btn = dialog.get_by_role("button", name=re.compile(r"Submit Request|Submit", re.I)).first
        submit_btn.click()
        self.page.wait_for_timeout(500)

        # Capture toast message
        toast = self.wait_for_toast_message()

        # Close dialog cleanly if still visible (e.g. when blocked by governance rule)
        try:
            if dialog.is_visible(timeout=500):
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
        except Exception:
            pass

        return {
            "success": True,
            "toast": toast or "",
            "category": selected_cat,
            "sub_category": selected_sub
        }

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
