import os
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
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-request", timeout=30000, wait_until="domcontentloaded")
        except Exception:
            self.page.goto(f"{settings.BASE_URL}/asset-request", timeout=30000)
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
                cancel_btn = dialog.get_by_role("button", name=re.compile(r"Cancel|Close", re.I)).first
                if cancel_btn.is_visible(timeout=1000):
                    cancel_btn.click()
                else:
                    self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)
        except Exception:
            pass

        return {
            "success": True,
            "toast": toast or "",
            "category": selected_cat,
            "sub_category": selected_sub
        }

    def request_asset_return(
        self,
        asset_code_or_name: str = None,
        reason: str = "Project concluded / Hardware upgrade required",
        return_date: str = "2026-08-26",
        upload_media: bool = True,
        media_files: list[str] = None,
        **kwargs
    ) -> dict:
        """
        Employee-Initiated Return Request:
        1. Identifies the target active assigned asset row in the Employee portal (/asset-request).
        2. Clicks the action column button: locator("//button[@aria-label='Return asset']//*[name()='svg']")
        3. Fills the 'Return Request' modal:
           - Header: <p class="chakra-text css-1mzljxq">Request Asset Return</p>
           - Media Upload: <p class="chakra-text css-ixa7ci">Click to upload images or video</p>
             (Attaches up to 4 photos each <= 5MB and 1 video ~10s)
           - Reason textarea
           - Return Date (if available)
        4. Clicks 'Submit Request' / 'Confirm'.
        5. Captures and returns toast confirmation.
        """
        from utils.asset_media_helper import get_return_test_media_files

        logger.info(f"Initiating Employee Return Request for asset: '{asset_code_or_name or 'First Assigned'}'")
        self.page.wait_for_timeout(1000)

        # 1. Locate the return action button
        ret_btn = None
        if asset_code_or_name:
            target_row = self.page.locator("table tbody tr, .chakra-card, .css-prwjms").filter(has_text=asset_code_or_name).first
            if target_row.is_visible(timeout=2000):
                ret_btn = target_row.locator("xpath=.//button[@aria-label='Return asset'] | .//button[@aria-label='Return Asset'] | .//button[contains(@aria-label, 'Return')]").first
                if not ret_btn.is_visible(timeout=500):
                    ret_btn = target_row.get_by_role("button", name=re.compile(r"Return|Request Return", re.I)).first

        if not ret_btn or not ret_btn.is_visible(timeout=500):
            # Fallback to the dedicated aria-label button locator on the table
            ret_btn = self.page.locator("//button[@aria-label='Return asset'] | //button[@aria-label='Return Asset']").first
            if not ret_btn.is_visible(timeout=1000):
                ret_btn = self.page.locator("//button[contains(@aria-label, 'Return')]//*[name()='svg']/..").first
            if not ret_btn.is_visible(timeout=1000):
                ret_btn = self.page.get_by_role("button", name=re.compile(r"Return Asset|Request Return|Return", re.I)).first

        if not ret_btn.is_visible(timeout=3000):
            logger.warning(f"Return button not found on /asset-request for asset: '{asset_code_or_name}'")
            return {"success": False, "toast": "Return button not visible"}

        logger.info("Clicking Action Column -> 'Return asset' button...")
        ret_btn.scroll_into_view_if_needed()
        try:
            ret_btn.click(timeout=3000)
        except Exception:
            ret_btn.click(force=True)

        self.page.wait_for_timeout(800)

        # 2. Handle Return Request Modal
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if not dialog.is_visible(timeout=3000):
            dialog = self.page.locator("div.chakra-modal__content").first

        if dialog.is_visible(timeout=4000):
            # 2.1 Media Attachment Upload (Up to 4 photos <= 5MB + 1 video ~10s)
            if upload_media:
                try:
                    files_to_upload = media_files or get_return_test_media_files(include_video=True, max_photos=4)
                    file_input = dialog.locator("input[type='file']").first
                    if not file_input.is_visible(timeout=500):
                        file_input = self.page.locator("input[type='file']").first

                    if file_input.count() > 0 and files_to_upload:
                        file_input.set_input_files(files_to_upload)
                        self.page.wait_for_timeout(1000)
                        logger.info(f"Attached {len(files_to_upload)} media files to Return Request modal: {[os.path.basename(f) for f in files_to_upload]}")
                except Exception as ex:
                    logger.warning(f"Media upload note in return modal: {ex}")

            # 2.2 Fill Reason
            try:
                reason_in = dialog.locator("textarea, input[placeholder*='reason' i], [name*='reason' i]").first
                if not reason_in.is_visible(timeout=1000):
                    reason_in = dialog.get_by_placeholder(re.compile(r"Reason|Remarks|Why", re.I)).first
                if reason_in.is_visible(timeout=1000):
                    reason_in.fill(reason)
                    logger.info(f"Filled Return Reason: '{reason}'")
            except Exception as ex:
                logger.warning(f"Return reason fill note: {ex}")

            # 2.3 Fill Date if requested
            if return_date:
                try:
                    date_in = dialog.locator("input[type='date']").first
                    if date_in.is_visible(timeout=500):
                        date_in.fill(return_date)
                        logger.info(f"Filled Return Date: '{return_date}'")
                except Exception:
                    pass

            # 2.4 Click Submit Request / Confirm
            submit_btn = dialog.get_by_role("button", name=re.compile(r"Submit Request|Submit|Return Asset|Return|Confirm|Proceed", re.I)).first
            if not submit_btn.is_visible(timeout=1000):
                submit_btn = dialog.locator("button.chakra-button, button[type='submit']").filter(has_text=re.compile(r"Submit|Return|Confirm", re.I)).first

            logger.info("Clicking modal 'Submit Request' button...")
            submit_btn.scroll_into_view_if_needed()
            try:
                submit_btn.click(timeout=3000)
            except Exception:
                submit_btn.click(force=True)

        # 3. Capture Toast
        toast = self.wait_for_toast_message()
        logger.info(f"Captured Employee Return Request Toast: '{toast}'")

        # Clean dialog close if blocked or lingering
        try:
            if dialog.is_visible(timeout=500):
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
        except Exception:
            pass

        return {
            "success": any(term in toast.lower() for term in ["success", "submitted", "requested", "created"]),
            "toast": toast
        }

    def request_return(self, asset_code_or_name: str) -> bool:
        """Backward-compatible alias for request_asset_return."""
        res = self.request_asset_return(asset_code_or_name=asset_code_or_name)
        return res.get("success", False)

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
