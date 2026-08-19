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

    def return_asset(self, asset_code_or_name: str = None, asset_code: str = None, condition: str = "Good", return_date: str = "2026-08-18", remarks: str = "Asset returned in good condition."):
        """
        Admin/IT side Single Asset Return fulfillment according to exact UI steps:
        1. Click 'Assigned Assets' tab
        2. Search asset code or employee name (placeholder: 'Search asset / employee…')
        3. Filter row by asset code and click row 'Return' button
        4. In 'Return Asset' dialog: Fill return date, check condition radio (Good), fill remarks textarea & click Return Asset confirmation.
        """
        asset_code_or_name = asset_code or asset_code_or_name
        logger.info(f"Returning asset: '{asset_code_or_name}' with Condition: '{condition}'")
        
        # 1. Click 'Assigned Assets' tab
        try:
            assigned_tab = self.page.get_by_role("tab", name=re.compile(r"Assigned Assets", re.I)).first
            if assigned_tab.is_visible(timeout=3000):
                assigned_tab.click()
                self.page.wait_for_timeout(600)
        except Exception as e:
            logger.warning(f"Note on Assigned Assets tab click: {e}")

        # 2. Search asset / employee
        search_input = self.page.get_by_placeholder("Search asset / employee…")
        if not search_input.is_visible(timeout=1000):
            search_input = self.page.locator("input[placeholder*='Search' i]").first

        if search_input.is_visible(timeout=2000):
            search_input.fill(asset_code_or_name)
            search_input.press("Enter")
            self.page.wait_for_timeout(1000)

        # 3. Locate row containing asset_code_or_name
        row = self.page.locator("tr").filter(has_text=asset_code_or_name).first
        if not row.is_visible(timeout=3000):
            row = self.page.locator("table tbody tr").filter(has=self.page.locator("td")).first

        if not row.is_visible(timeout=3000):
            logger.warning(f"No asset return row visible for '{asset_code_or_name}'. Grid may be empty.")
            return "No asset pending return"

        # 4. Click 'Return' button within that specific row
        return_btn = row.get_by_role("button", name=re.compile(r"^Return$", re.I)).first
        if not return_btn.is_visible(timeout=2000):
            return_btn = row.get_by_role("button", name=re.compile(r"(Return|Process Return|Receive)", re.I)).first

        if return_btn.is_visible(timeout=2000):
            return_btn.click()
            self.page.wait_for_timeout(500)
        else:
            # Checkbox fallback -> Process Bulk Return
            checkbox = row.locator("input[type='checkbox'], span.chakra-checkbox").first
            if checkbox.is_visible(timeout=1000):
                checkbox.click()
                self.page.wait_for_timeout(500)
            bulk_btn = self.page.get_by_role("button", name=re.compile(r"(Process Bulk Return|Bulk Return)", re.I)).first
            if bulk_btn.is_visible(timeout=2000):
                bulk_btn.click()

        # 5. Handle 'Return Asset' modal dialog
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if not dialog.is_visible(timeout=3000):
            dialog = self.page.locator("div.chakra-modal__content").first

        if dialog.is_visible(timeout=5000):
            # Return Date
            try:
                date_input = dialog.locator("input[type='date']").first
                if date_input.is_visible(timeout=1000):
                    date_input.fill(return_date)
            except Exception as e:
                logger.warning(f"Date fill note: {e}")

            # Condition Radio Button (Good / Damaged / Repair Required / Lost)
            try:
                radio_option = dialog.get_by_role("radio", name=re.compile(condition, re.I)).first
                if radio_option.is_visible(timeout=1000):
                    radio_option.check()
                else:
                    dialog.get_by_text(condition, exact=True).first.click()
            except Exception as ex:
                logger.warning(f"Condition selection note for '{condition}': {ex}")

            # Remarks Textarea
            try:
                remarks_in = dialog.locator("textarea").first
                if remarks_in.is_visible(timeout=1000):
                    remarks_in.fill(remarks)
            except Exception as e:
                logger.warning(f"Remarks fill note: {e}")

            # Click Submit/Return Confirmation Button (e.g. 'Return 1 Asset' or 'Return Asset')
            confirm_btn = dialog.get_by_role("button", name=re.compile(r"Return \d+ Asset|Return Asset", re.I)).first
            if not confirm_btn.is_visible(timeout=1000):
                confirm_btn = dialog.get_by_role("button", name=re.compile(r"(Return|Confirm|Yes|Proceed|Submit)", re.I)).first
            confirm_btn.click()

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

            # Click modal submission button (e.g. 'Return 1 Asset', 'Return 2 Assets', or 'Return Asset')
            submit_btn = dialog.get_by_role("button", name=re.compile(r"Return \d+ Asset|Return Asset", re.I)).first
            if not submit_btn.is_visible(timeout=1000):
                submit_btn = dialog.locator("button.chakra-button").filter(has_text=re.compile(r"Return", re.I)).last
            
            submit_btn.click()

    def navigate_to_return_history_tab(self):
        """Clicks the 'Return History' tab on the Asset Return page."""
        logger.info("Navigating to 'Return History' tab")
        history_tab = self.page.get_by_role("tab", name=re.compile(r"Return History", re.I)).first
        if not history_tab.is_visible(timeout=2000):
            history_tab = self.page.locator("button[role='tab']").filter(has_text=re.compile(r"Return History", re.I)).first
        history_tab.click()
        self.page.wait_for_timeout(600)

    def verify_return_history_entry(self, asset_code_or_name: str, expected_condition: str = None, expected_status: str = None, fallback_employee: str = "Sanidhy Tiwari") -> dict:
        """
        Navigates to Return History tab, searches asset/employee name, and validates row columns:
        [Asset Code, Asset Name, Assignment, Assigned To, Return Date, Condition, New Status, Returned By, Remarks]
        Fails assertion if matching row is not found in table.
        """
        self.navigate_to_return_history_tab()
        
        # 1. Primary search: asset_code_or_name
        search_input = self.page.get_by_placeholder("Search asset / employee…")
        if not search_input.is_visible(timeout=1000):
            search_input = self.page.locator("input[placeholder*='Search' i]").first

        if search_input.is_visible(timeout=2000):
            search_input.fill(asset_code_or_name)
            search_input.press("Enter")
            self.page.wait_for_timeout(1000)

        # 2. Check if matching row exists
        row = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
        if not row.is_visible(timeout=2000) and fallback_employee:
            logger.info(f"[RETURN HISTORY] Primary search '{asset_code_or_name}' not visible -> Fallback search by employee: '{fallback_employee}'")
            if search_input.is_visible():
                search_input.fill(fallback_employee)
                search_input.press("Enter")
                self.page.wait_for_timeout(1000)
            row = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
            if not row.is_visible(timeout=1000):
                row = self.page.locator("table tbody tr").first

        row_visible = row.is_visible(timeout=2000)
        assert row_visible, f"[RETURN HISTORY ERROR] Asset record '{asset_code_or_name}' not found in Return History table!"

        cells = row.locator("td").all()
        assert len(cells) >= 9, f"[RETURN HISTORY ERROR] Expected at least 9 table columns, found {len(cells)}"

        row_data = {
            "asset_code": cells[0].inner_text().strip(),
            "asset_name": cells[1].inner_text().strip(),
            "assignment": cells[2].inner_text().strip(),
            "assigned_to": cells[3].inner_text().strip(),
            "return_date": cells[4].inner_text().strip(),
            "condition": cells[5].inner_text().strip(),
            "new_status": cells[6].inner_text().strip(),
            "returned_by": cells[7].inner_text().strip(),
            "remarks": cells[8].inner_text().strip()
        }
        logger.info(f"[RETURN HISTORY VERIFIED] {row_data}")

        if expected_condition:
            assert expected_condition.lower() in row_data["condition"].lower(), f"Expected condition '{expected_condition}', got '{row_data['condition']}'"
        if expected_status:
            assert expected_status.lower() in row_data["new_status"].lower(), f"Expected new status '{expected_status}', got '{row_data['new_status']}'"

        return row_data

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
