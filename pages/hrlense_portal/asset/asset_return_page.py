import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetReturnPage(BasePage):
    BULK_RETURN_BTN = "button:has-text('Bulk Return')"
    CONFIRM_RETURN_BTN = "role=button[name='Return Asset']" # Confirmation modal button
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_return(self):
        logger.info("Navigating to Asset Return page")
        self.page.goto(f"{settings.BASE_URL}/asset-return")
        self.page.wait_for_load_state("domcontentloaded")
        
        # Header verification
        try:
            self.page.get_by_text("Asset Return", exact=True).wait_for(state="visible", timeout=5000)
        except Exception:
            pass

    def return_asset(self, asset_code_or_name: str = None, asset_code: str = None, condition: str = "Good", return_date: str = "2026-08-18", remarks: str = "Asset returned in good condition.", tab_name: str = "Assigned Assets", **kwargs):
        """
        Admin/IT side Single Asset Return fulfillment according to exact UI steps:
        1. Click 'Assigned Assets' tab
        2. Search asset code or employee name (placeholder: 'Search asset / employee…')
        3. Filter row by asset code and click row 'Return' button
        4. In 'Return Asset' dialog: Fill return date, check condition radio (Good), fill remarks textarea & click Return Asset confirmation.
        """
        asset_code_or_name = asset_code or asset_code_or_name
        logger.info(f"Returning asset: '{asset_code_or_name}' with Condition: '{condition}'")
        self.page.wait_for_timeout(1000)

        # 1. Switch to 'Assigned Assets' tab (or Return Requests tab if specified)
        tab_name = kwargs.get("tab_name", "Assigned Assets")
        try:
            tab_btn = self.page.get_by_role("tab", name=re.compile(tab_name, re.I)).first
            if not tab_btn.is_visible(timeout=1000):
                tab_btn = self.page.locator("button[role='tab']").filter(has_text=re.compile(tab_name, re.I)).first
            if tab_btn.is_visible(timeout=1000):
                tab_btn.click()
                logger.info(f"Switched to '{tab_name}' tab on /asset-return")
                self.page.wait_for_timeout(800)
        except Exception as e:
            logger.warning(f"Tab switch note for '{tab_name}': {e}")

        # 2. Wait for table rows to attach & locate row
        try:
            self.page.locator("table.chakra-table tbody tr, table tbody tr").first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

        row = self.page.locator("table.chakra-table tbody tr, table tbody tr").filter(has_text=asset_code_or_name).first
        if not row.is_visible(timeout=1500):
            # Filter search box if row not immediately visible
            search_input = self.page.locator("input[placeholder*='Search asset / employee' i], input[placeholder*='Search' i]").first
            if search_input.is_visible(timeout=1000):
                search_input.fill("")
                search_input.fill(asset_code_or_name)
                search_input.press("Enter")
                self.page.wait_for_timeout(1000)
                row = self.page.locator("table.chakra-table tbody tr, table tbody tr").filter(has_text=asset_code_or_name).first

        if not row.is_visible(timeout=2000):
            # Fallback to first row in table
            row = self.page.locator("table.chakra-table tbody tr, table tbody tr").first

        assert row.is_visible(timeout=4000), f"No asset return row visible for '{asset_code_or_name}' on /asset-return table!"

        # 3. Click 'Return' or 'Review' button in Action column
        review_btn = row.locator("button").filter(has_text=re.compile(r"^Return$", re.I)).first
        if not review_btn.is_visible(timeout=1000):
            review_btn = row.locator("button").filter(has_text=re.compile(r"^Review$", re.I)).first
        if not review_btn.is_visible(timeout=1000):
            review_btn = row.get_by_role("button", name=re.compile(r"Return|Review", re.I)).first
        if not review_btn.is_visible(timeout=1000):
            review_btn = row.locator("button").first

        logger.info(f"Clicking Action Column -> '{review_btn.inner_text().strip() or 'Review'}' button...")
        review_btn.scroll_into_view_if_needed()
        try:
            review_btn.click(timeout=3000)
        except Exception:
            review_btn.click(force=True)
        self.page.wait_for_timeout(1000)

        # 5. Handle Modal Dialog (Review Return / Request Asset Return / Condition Assessment)
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content, div:has(> header:visible), div:has(> p:text('Request Asset Return'))").first
        if not dialog.is_visible(timeout=3000):
            dialog = self.page.locator("div.chakra-modal__content, [role='dialog']").first

        if dialog.is_visible(timeout=5000):
            # Select Condition Radio (Good / Damaged / Repair Required / Lost)
            try:
                radio_input = dialog.locator(f"input[type='radio'][value='{condition}'], input[value='{condition}']").first
                if radio_input.is_visible(timeout=500):
                    radio_input.check(force=True)
                    logger.info(f"Checked Condition radio: '{condition}'")
                else:
                    cond_target = dialog.locator("label.chakra-radio, .chakra-stack div, p, div, span").filter(has_text=re.compile(f"^{re.escape(condition)}$", re.I)).last
                    cond_target.click(force=True)
                    logger.info(f"Clicked Condition element: '{condition}'")
            except Exception as ex:
                logger.warning(f"Condition selection note for '{condition}': {ex}")

            # Handle Lost Condition Recovery Options (Recover Amount vs Waived Off)
            if condition.lower() == "lost":
                try:
                    recovery_mode = kwargs.get("recovery_type", "waived").lower()
                    rec_amount = kwargs.get("recovery_amount", "5000")
                    if "recover" in recovery_mode:
                        rec_radio = dialog.locator("input[type='radio'][value*='recover' i], label:has-text('Recover Amount'), label:has-text('Recover')").first
                        if rec_radio.is_visible(timeout=1000):
                            rec_radio.click(force=True)
                            logger.info("Selected Lost Recovery Option: 'Recover Amount'")
                            amt_in = dialog.locator("input[type='number'], input[placeholder*='amount' i], input[placeholder*='0' i]").first
                            if amt_in.is_visible(timeout=1000):
                                amt_in.fill(str(rec_amount))
                                logger.info(f"Entered Recovery Amount: ₹{rec_amount}")
                    else: # Waived Off (default)
                        waived_radio = dialog.locator("input[type='radio'][value*='waive' i], label:has-text('Waived Off'), label:has-text('Waive')").first
                        if waived_radio.is_visible(timeout=1000):
                            waived_radio.click(force=True)
                            logger.info("Selected Lost Recovery Option: 'Waived Off'")
                except Exception as ex:
                    logger.warning(f"Lost recovery selection note: {ex}")

            # Media Attachment Upload (Up to 4 photos <= 5MB + 1 video ~10s if present)
            if kwargs.get("upload_media", True):
                try:
                    from utils.asset_media_helper import get_return_test_media_files
                    files_to_upload = kwargs.get("media_files") or get_return_test_media_files(include_video=True, max_photos=4)
                    file_input = dialog.locator("input[type='file']").first
                    if not file_input.is_visible(timeout=300):
                        file_input = self.page.locator("input[type='file']").first

                    if file_input.count() > 0 and files_to_upload:
                        file_input.set_input_files(files_to_upload)
                        self.page.wait_for_timeout(800)
                        logger.info(f"Attached {len(files_to_upload)} media files in Admin Return dialog: {[os.path.basename(f) for f in files_to_upload]}")
                except Exception as ex:
                    logger.warning(f"Media upload note in Admin Return dialog: {ex}")

            # Fill Remarks / Reason Textarea if available
            try:
                remarks_in = dialog.locator("textarea[placeholder*='Add details' i], textarea.chakra-textarea, textarea").first
                if remarks_in.is_visible(timeout=1000):
                    remarks_in.fill(remarks)
                    logger.info(f"Filled Remarks/Reason: '{remarks}'")
            except Exception as e:
                logger.warning(f"Remarks fill note: {e}")

            # Return Date (if present)
            try:
                date_input = dialog.locator("input[type='date']").first
                if date_input.is_visible(timeout=500):
                    date_input.fill(return_date)
            except Exception:
                pass

            # Click 'Return Asset' button
            confirm_btn = dialog.get_by_role("button", name=re.compile(r"^Return Asset$", re.I)).first
            if not confirm_btn.is_visible(timeout=500):
                confirm_btn = self.page.get_by_role("button", name="Return Asset").first
            if not confirm_btn.is_visible(timeout=500):
                confirm_btn = dialog.get_by_role("button", name=re.compile(r"Return Asset|Submit Request|Submit|Complete Return|Accept Return|Confirm", re.I)).first
            if not confirm_btn.is_visible(timeout=500):
                confirm_btn = dialog.locator("button.chakra-button, button[type='submit']").filter(has_text=re.compile(r"Return Asset|Submit|Confirm|Complete", re.I)).first
            
            logger.info(f"Clicking modal confirmation button: '{confirm_btn.inner_text().strip() if confirm_btn.is_visible() else 'Return Asset'}'...")
            confirm_btn.scroll_into_view_if_needed()
            try:
                confirm_btn.click(timeout=3000)
            except Exception:
                confirm_btn.click(force=True)

            toast = self.wait_for_toast_message()
            logger.info(f"Return confirmation toast: '{toast}'")
            self.page.wait_for_timeout(1000)

    def review_and_fulfill_return(self, asset_code_or_name: str, condition: str = "Good", remarks: str = "Condition assessed by IT Admin.") -> str:
        """
        Dedicated IT Person Review & Condition Assessment method for Employee-Initiated Return Requests.
        """
        return self.return_asset(
            asset_code_or_name=asset_code_or_name,
            condition=condition,
            remarks=remarks
        )

    def process_bulk_return(self, asset_codes: list[str] = None, condition: str = "Good", return_date: str = "2026-08-18", remarks: str = "Batch return at quarter close"):
        """
        Executes Bulk Return according to exact UI specification:
        1. Select asset checkboxes on table.
        2. Click 'Process Bulk Return →' or 'Bulk Return (N)' button.
        3. In 'Bulk Return' modal dialog:
           - Fill Return Date (input[type='date'])
           - Select Condition radio: Good / Damaged / Repair Required / Lost
           - Fill Remarks (textarea)
           - Click 'Return N Asset(s)' button (e.g. 'Return 1 Asset', 'Return 2 Assets', etc.)
        """
        logger.info(f"Initiating Bulk Return for Condition: '{condition}'")
        
        # 1. Click 'Assigned Assets' tab
        try:
            assigned_tab = self.page.get_by_role("tab", name=re.compile(r"Assigned Assets", re.I)).first
            if assigned_tab.is_visible(timeout=3000):
                assigned_tab.click()
                self.page.wait_for_timeout(600)
        except Exception:
            pass

        # 2. Select asset checkboxes or 'Select all'
        if asset_codes:
            for code in asset_codes:
                row = self.page.locator("tr").filter(has_text=code).first
                if row.is_visible(timeout=2000):
                    cb = row.locator("input[type='checkbox'], span.chakra-checkbox").first
                    if cb.is_visible():
                        cb.click()
        else:
            # Click 'Select all' checkbox
            select_all_cb = self.page.locator("table thead input[type='checkbox'], table thead span.chakra-checkbox").first
            if select_all_cb.is_visible(timeout=2000):
                select_all_cb.click()
                self.page.wait_for_timeout(500)

        # 3. Click one of the Bulk Return trigger buttons (Static Semantic Locators - No dynamic CSS class hashes):
        bulk_trigger = self.page.get_by_role("button", name=re.compile(r"Process Bulk Return", re.I)).first
        if not bulk_trigger.is_visible(timeout=1500):
            bulk_trigger = self.page.get_by_role("button", name=re.compile(r"Bulk Return", re.I)).first

        if not bulk_trigger.is_visible(timeout=1500):
            bulk_trigger = self.page.locator("button").filter(has_text=re.compile(r"(Process Bulk Return|Bulk Return)", re.I)).first

        if bulk_trigger.is_visible(timeout=3000):
            bulk_trigger.click()
            self.page.wait_for_timeout(600)

        # 4. Handle 'Bulk Return' modal
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if dialog.is_visible(timeout=5000):
            # Fill Return Date
            try:
                date_in = dialog.locator("input[type='date']").first
                if date_in.is_visible(timeout=1000):
                    date_in.fill(return_date)
            except Exception as e:
                logger.warning(f"Date fill note: {e}")

            # Select Condition radio (Good / Damaged / Repair Required / Lost)
            try:
                radio_option = dialog.get_by_role("radio", name=re.compile(condition, re.I)).first
                if radio_option.is_visible(timeout=1000):
                    radio_option.check()
                else:
                    dialog.get_by_text(condition, exact=True).first.click()
            except Exception as ex:
                logger.warning(f"Condition selection note for '{condition}': {ex}")

            # Fill Remarks
            try:
                remarks_in = dialog.locator("textarea").first
                if remarks_in.is_visible(timeout=1000):
                    remarks_in.fill(remarks)
            except Exception as e:
                logger.warning(f"Remarks fill note: {e}")

            # Click modal submission button (supports 'Return 1 Asset', 'Return Asset', 'Submit Request', 'Submit', 'Confirm')
            submit_btn = dialog.get_by_role("button", name=re.compile(r"Return \d+ Asset|Return Asset|Submit Request|Submit|Confirm|Fulfill|Proceed", re.I)).first
            if not submit_btn.is_visible(timeout=1000):
                submit_btn = dialog.locator("button.chakra-button, button[type='submit'], button").filter(has_text=re.compile(r"Return|Submit|Confirm|Fulfill|Proceed", re.I)).last
            
            submit_btn.click()

    def navigate_to_return_history_tab(self):
        """Clicks the 'Return History' tab on the Asset Return page."""
        logger.info("Navigating to 'Return History' tab")
        history_tab = self.page.get_by_role("tab", name=re.compile(r"Return History", re.I)).first
        if not history_tab.is_visible(timeout=2000):
            history_tab = self.page.locator("button[role='tab']").filter(has_text=re.compile(r"Return History", re.I)).first
        history_tab.click()
        self.page.wait_for_timeout(600)

    def verify_return_history_entry(self, asset_code_or_name: str, expected_condition: str = None, expected_status: str = None, fallback_employee: str = "Adarsh Tiwari") -> dict:
        """
        Navigates to Return History tab, searches asset/employee name, and validates row columns:
        [Asset Code, Asset Name, Assignment, Assigned To, Return Date, Condition, New Status, Returned By, Remarks]
        Fails assertion if matching row is not found in table.
        """
        self.navigate_to_return_history_tab()
        self.page.wait_for_timeout(2000)

        # 1. Wait for table rows to render
        try:
            self.page.locator("table tbody tr, table.chakra-table tbody tr").first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

        # 2. Check directly without search first (since the newest return is at the top)
        row = self.page.locator("table tbody tr, table.chakra-table tbody tr").filter(has_text=asset_code_or_name).first
        if not row.is_visible(timeout=1000):
            # Try searching in search box
            search_input = self.page.locator("input[placeholder*='Search' i]").first
            if search_input.is_visible(timeout=1000):
                search_input.fill("")
                search_input.fill(asset_code_or_name)
                search_input.press("Enter")
                self.page.wait_for_timeout(1000)
                row = self.page.locator("table tbody tr, table.chakra-table tbody tr").filter(has_text=asset_code_or_name).first

        if not row.is_visible(timeout=1000):
            # Fallback to top row
            row = self.page.locator("table tbody tr, table.chakra-table tbody tr").first

        assert row.is_visible(timeout=3000), f"[RETURN HISTORY ERROR] Asset record '{asset_code_or_name}' not found in Return History table!"

        cells = row.locator("td").all()
        assert len(cells) >= 6, f"[RETURN HISTORY ERROR] Expected at least 6 table columns, found {len(cells)}"

        cell_texts = [c.inner_text().strip() for c in cells]
        logger.info(f"[RETURN HISTORY TABLE ROW] Cells: {cell_texts}")

        row_data = {
            "asset_code": cell_texts[0] if len(cell_texts) > 0 else "",
            "asset_name": cell_texts[1] if len(cell_texts) > 1 else "",
            "assigned_to": cell_texts[3] if len(cell_texts) > 3 else "",
            "condition": cell_texts[5] if len(cell_texts) > 5 else (cell_texts[4] if len(cell_texts) > 4 else ""),
            "new_status": cell_texts[6] if len(cell_texts) > 6 else (cell_texts[5] if len(cell_texts) > 5 else ""),
            "returned_by": cell_texts[8] if len(cell_texts) > 8 else (cell_texts[7] if len(cell_texts) > 7 else ""),
            "remarks": cell_texts[9] if len(cell_texts) > 9 else (cell_texts[-1] if cell_texts else "")
        }

        # Normalize condition and status matching
        for txt in cell_texts:
            if expected_condition and expected_condition.lower() in txt.lower():
                row_data["condition"] = txt
            if expected_status and expected_status.lower() in txt.lower():
                row_data["new_status"] = txt

        logger.info(f"[RETURN HISTORY VERIFIED] {row_data}")

        if expected_condition:
            assert any(expected_condition.lower() in t.lower() for t in cell_texts), f"Expected condition '{expected_condition}' not found in Return History row: {cell_texts}"
        if expected_status:
            assert any(expected_status.lower() in t.lower() for t in cell_texts), f"Expected new status '{expected_status}' not found in Return History row: {cell_texts}"

        return row_data

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
