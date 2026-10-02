"""
Branch Master & Manage Signatures Page Object (HR Lens Portal).
Handles Branch Master table interactions and the "Manage Signatures" modal.
URL Route: /master/branch
"""

import logging
from typing import Dict, List, Optional
from playwright.sync_api import Locator
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class BranchPage(BasePage):
    ROUTE_URL = f"{settings.BASE_URL}/master/branch"

    # Branch Master Page Header & Actions
    PAGE_TITLE = "p:has-text('Branch')"
    ADD_BRANCH_BTN = "button:has-text('Add New Branch')"

    # Branch Master Table Locators
    BRANCH_TABLE = "table.chakra-table"
    BRANCH_TABLE_ROWS = "table.chakra-table tbody tr"
    SIGNATURE_ACTION_BTN = "button[aria-label='signature']"
    EDIT_BRANCH_ACTION_BTN = "button[aria-label='Edit']"
    VIEW_SIGNATURE_BTN = "td:nth-child(10) button:has-text('View')"

    # Manage Signatures Modal Locators
    MODAL_CONTAINER = "div[role='dialog']:has-text('Manage Signatures'), .chakra-modal__content:has-text('Manage Signatures')"
    MODAL_HEADER = "header.chakra-modal__header, [id*='chakra-modal--header']"
    MODAL_CLOSE_BTN = "button[aria-label='Close']"

    # Scope Checkboxes
    DEFAULT_CHECKBOX = "label.chakra-checkbox:has-text('Set as Default')"
    PAYSLIP_CHECKBOX = "label.chakra-checkbox:has-text('For Payslip')"
    ONBOARDING_CHECKBOX = "label.chakra-checkbox:has-text('For Onboarding Letters')"

    # Employee Search & Add
    CARD_CONTAINER = ".css-4qyjep"
    SEARCH_EMPLOYEE_INPUT = "input[placeholder='Search employee...']"
    DROPDOWN_SUGGESTION = ".css-1creex5 div, .css-17ezq3"
    UPLOAD_CONTAINER = ".css-1ayfwcb"
    FILE_INPUT = ".css-1ayfwcb input[type='file'], input[type='file'][accept='image/*']"
    BLOCK_CANCEL_BTN = ".css-1ayfwcb button:has-text('Cancel'), .chakra-form__label:has-text('Upload Signature') ~ * button:has-text('Cancel')"
    ADD_MORE_BTN = "button:has-text('Add More')"

    # Default Signature File Path in Test Data
    DEFAULT_SIGNATURE_PATH = "testdata/static/image/signature.png"

    # Signature List Table inside Modal
    SIGNATURE_SEARCH_INPUT = "input[placeholder='Search...']"
    COLUMNS_MENU_BTN = "button[aria-label='Columns']"
    SIGNATURE_TABLE = "table.chakra-table"
    SIGNATURE_ROWS = "div[role='dialog'] table.chakra-table tbody tr, .chakra-modal__content table.chakra-table tbody tr"

    # Modal Action Buttons
    CANCEL_BTN = "footer.chakra-modal__footer button:has-text('Cancel'), button:has-text('Cancel')"
    SUBMIT_BTN = "footer.chakra-modal__footer button:has-text('Submit'), button:has-text('Submit')"

    def navigate_to_branch_master(self):
        """Navigates directly to the Branch Master page."""
        logger.info(f"Navigating to Branch Master: {self.ROUTE_URL}")
        if "/master/branch" not in self.page.url:
            self.page.goto(self.ROUTE_URL, timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_selector(self.BRANCH_TABLE, timeout=15000)

        # Expand page size to 100 so all branches (Agra, Varanasi, etc.) across all companies are visible
        try:
            page_size_select = self.page.locator(".pagination ~ .chakra-select__wrapper select, select.chakra-select").last
            if page_size_select.is_visible(timeout=2000):
                if page_size_select.input_value() != "100":
                    page_size_select.select_option("100")
                    self.page.wait_for_timeout(1500)
                    self.page.locator(self.BRANCH_TABLE_ROWS).first.wait_for(state="visible", timeout=5000)
                    logger.info("Expanded Branch Master pagination to 100 rows.")
        except Exception:
            pass

    def get_modal(self) -> Locator:
        """Returns the Manage Signatures modal dialog locator."""
        return self.page.locator(self.MODAL_CONTAINER).first

    def is_manage_signatures_modal_open(self) -> bool:
        """Checks if the Manage Signatures modal is currently visible."""
        try:
            return self.get_modal().is_visible(timeout=3000)
        except Exception:
            return False

    def open_manage_signatures_for_branch(
        self, branch_name: Optional[str] = None, company_name: Optional[str] = None
    ):
        """
        Opens Manage Signatures modal by clicking the action button in the branch row.
        Filters by branch_name (e.g. 'Agra', 'Varanasi') and optionally company_name (e.g. 'TEK Inspirations LLC').
        """
        self.navigate_to_branch_master()

        rows = self.page.locator(self.BRANCH_TABLE_ROWS)
        if branch_name:
            logger.info(f"Locating branch row for branch: '{branch_name}', company: '{company_name}'")
            filtered = rows.filter(has_text=branch_name)
            if company_name:
                filtered = filtered.filter(has_text=company_name)
            row = filtered.first
        else:
            logger.info("Opening Manage Signatures for the first available branch.")
            row = rows.first

        row.wait_for(state="visible", timeout=10000)
        row.scroll_into_view_if_needed()

        # Locate Action button inside row (exact aria-label='signature' from Branch Master DOM)
        action_btn = row.locator(self.SIGNATURE_ACTION_BTN).first
        if not action_btn.is_visible():
            action_btn = row.locator("button[aria-label*='signature' i], button:has-text('+'), td:last-child button:last-child").first
        
        action_btn.scroll_into_view_if_needed()
        action_btn.wait_for(state="visible", timeout=5000)
        action_btn.click(force=True)

        # Wait for modal to appear
        modal = self.get_modal()
        modal.wait_for(state="visible", timeout=10000)
        logger.info("Manage Signatures modal successfully opened.")

    def _set_checkbox_state(self, label_selector: str, target_state: bool, parent: Optional[Locator] = None):
        """Sets a Chakra checkbox to the desired state (True for checked, False for unchecked)."""
        ctx = parent if parent is not None else self.get_modal()
        checkbox_label = ctx.locator(label_selector).first
        checkbox_input = checkbox_label.locator("input[type='checkbox']").first

        is_checked = checkbox_input.is_checked()
        if is_checked != target_state:
            checkbox_label.click()
            logger.info(f"Toggled checkbox '{label_selector}' from {is_checked} to {target_state}")

    def configure_scopes(
        self,
        default: Optional[bool] = None,
        payslip: Optional[bool] = None,
        onboarding: Optional[bool] = None,
        block_index: int = 0
    ):
        """Configures the scope checkboxes (multi-select) at top of the signature block."""
        modal = self.get_modal()
        cards = modal.locator(self.CARD_CONTAINER)
        card = cards.nth(block_index) if cards.count() > block_index else modal

        if default is not None:
            self._set_checkbox_state(self.DEFAULT_CHECKBOX, default, parent=card)
        if payslip is not None:
            self._set_checkbox_state(self.PAYSLIP_CHECKBOX, payslip, parent=card)
        if onboarding is not None:
            self._set_checkbox_state(self.ONBOARDING_CHECKBOX, onboarding, parent=card)

    def search_employee(self, employee_name: str, block_index: int = 0):
        """Types employee name in the 'Search Employee' input field of specified block."""
        modal = self.get_modal()
        cards = modal.locator(self.CARD_CONTAINER)
        card = cards.nth(block_index) if cards.count() > block_index else modal
        search_input = card.locator(self.SEARCH_EMPLOYEE_INPUT).first
        search_input.wait_for(state="visible", timeout=5000)
        search_input.fill("")
        search_input.fill(employee_name)
        logger.info(f"Filled employee search input (block {block_index}) with: '{employee_name}'")

    def select_employee_from_search(self, employee_name: str, block_index: int = 0):
        """
        Types employee name in search field, waits for autocomplete dropdown,
        and clicks the matching suggestion to reveal the Upload Signature block.
        """
        modal = self.get_modal()
        cards = modal.locator(self.CARD_CONTAINER)
        card = cards.nth(block_index) if cards.count() > block_index else modal
        search_input = card.locator(self.SEARCH_EMPLOYEE_INPUT).first
        search_input.wait_for(state="visible", timeout=5000)
        search_input.click()
        search_input.fill("")
        search_input.press_sequentially(employee_name, delay=100)
        self.page.wait_for_timeout(1000)

        # Dropdown suggestion appears inside .css-1creex5
        suggestion = card.locator(self.DROPDOWN_SUGGESTION).first
        if not suggestion.is_visible():
            suggestion = modal.locator(self.DROPDOWN_SUGGESTION).first

        suggestion.wait_for(state="visible", timeout=6000)
        suggestion_text = suggestion.inner_text().strip()
        logger.info(f"Selecting employee suggestion: '{suggestion_text}'")
        suggestion.click()

        # Wait for the upload container (.css-1ayfwcb) to appear
        upload_box = card.locator(self.UPLOAD_CONTAINER).first
        upload_box.wait_for(state="visible", timeout=6000)
        logger.info(f"Upload Signature box visible for '{suggestion_text}'")
        return suggestion_text

    def upload_signature(self, file_path: Optional[str] = None, block_index: int = 0):
        """
        Uploads a signature file to the file input.
        Defaults to 'testdata/static/image/signature.png' if not specified.
        """
        import os
        target_path = file_path or os.path.abspath(self.DEFAULT_SIGNATURE_PATH)
        assert os.path.exists(target_path), f"Signature file not found at: {target_path}"

        modal = self.get_modal()
        file_input = modal.locator(self.FILE_INPUT).nth(block_index)
        file_input.wait_for(state="attached", timeout=5000)
        file_input.set_input_files(target_path)
        logger.info(f"Attached signature file: {target_path} to block {block_index}")

    def click_block_cancel(self, block_index: int = 0):
        """Clicks Cancel on a specific signature upload block."""
        modal = self.get_modal()
        cards = modal.locator(self.CARD_CONTAINER)
        card = cards.nth(block_index) if cards.count() > block_index else modal
        cancel_btn = card.locator(".css-1ayfwcb button:has-text('Cancel'), .css-1n0is92 button:has-text('Cancel'), button:has-text('Cancel')").first
        cancel_btn.wait_for(state="visible", timeout=5000)
        cancel_btn.click()
        logger.info(f"Clicked in-block Cancel for block {block_index}")

    def click_add_more(self):
        """Clicks the 'Add More' button inside the modal."""
        modal = self.get_modal()
        add_btn = modal.locator(self.ADD_MORE_BTN).first
        add_btn.wait_for(state="visible", timeout=5000)
        add_btn.click()
        logger.info("Clicked 'Add More' button.")

    def search_signature_list(self, query: str):
        """Types a query in the Signature List table search bar."""
        modal = self.get_modal()
        table_search = modal.locator(self.SIGNATURE_SEARCH_INPUT).first
        table_search.wait_for(state="visible", timeout=5000)
        table_search.fill("")
        table_search.fill(query)
        self.page.wait_for_timeout(500)
        logger.info(f"Filtered signature list table by: '{query}'")

    def get_signature_list_records(self) -> List[Dict[str, any]]:
        """
        Parses all rows in the Signature List table inside the modal.
        Returns a list of dicts with:
        - s_no: str
        - employee_name: str
        - signature_img_src: str
        - is_default: bool
        - payslip: str
        - onboarding: str
        """
        modal = self.get_modal()
        rows = modal.locator(self.SIGNATURE_ROWS)
        count = rows.count()
        records = []

        for idx in range(count):
            row = rows.nth(idx)
            cells = row.locator("td")
            cell_count = cells.count()
            if cell_count < 6:
                continue

            s_no = cells.nth(0).inner_text().strip()
            emp_name = cells.nth(1).inner_text().strip()

            img = cells.nth(2).locator("img.chakra-image").first
            img_src = img.get_attribute("src") if img.count() > 0 else ""

            default_input = cells.nth(3).locator("input[type='checkbox']").first
            is_default = default_input.is_checked() if default_input.count() > 0 else False

            payslip_badge = cells.nth(4).locator(".chakra-badge").first
            payslip_text = payslip_badge.inner_text().strip() if payslip_badge.count() > 0 else cells.nth(4).inner_text().strip()

            onboarding_badge = cells.nth(5).locator(".chakra-badge").first
            onboarding_text = onboarding_badge.inner_text().strip() if onboarding_badge.count() > 0 else cells.nth(5).inner_text().strip()

            records.append({
                "s_no": s_no,
                "employee_name": emp_name,
                "signature_img_src": img_src,
                "is_default": is_default,
                "payslip": payslip_text,
                "onboarding": onboarding_text,
            })

        logger.info(f"Retrieved {len(records)} records from Signature List table.")
        return records

    def click_edit_signature(self, employee_name: str):
        """Clicks the edit button for a specific employee in the Signature List."""
        modal = self.get_modal()
        row = modal.locator(self.SIGNATURE_ROWS).filter(has_text=employee_name).first
        row.wait_for(state="visible", timeout=5000)
        edit_btn = row.locator("button[aria-label='Edit signature'], button:has-text('Edit'), td:last-child button").first
        edit_btn.click()
        logger.info(f"Clicked Edit signature for: '{employee_name}'")

    def click_submit(self):
        """Clicks Submit button inside modal footer."""
        modal = self.get_modal()
        submit_btn = modal.locator(self.SUBMIT_BTN).first
        submit_btn.wait_for(state="visible", timeout=5000)
        submit_btn.click()
        logger.info("Clicked Submit button in Manage Signatures modal.")

    def click_cancel(self):
        """Clicks Cancel button inside modal footer."""
        modal = self.get_modal()
        cancel_btn = modal.locator(self.CANCEL_BTN).first
        cancel_btn.wait_for(state="visible", timeout=5000)
        cancel_btn.click()
        logger.info("Clicked Cancel button in Manage Signatures modal.")

    def close_modal(self):
        """Closes the modal via the 'X' close button if currently open."""
        try:
            modal = self.get_modal()
            if modal.is_visible(timeout=1500):
                close_btn = modal.locator(self.MODAL_CLOSE_BTN).first
                if close_btn.is_visible(timeout=1500):
                    close_btn.click()
                    modal.wait_for(state="hidden", timeout=4000)
                    logger.info("Clicked Close (X) button on Manage Signatures modal.")
        except Exception as e:
            logger.debug(f"Modal already closed or close button not needed: {e}")
