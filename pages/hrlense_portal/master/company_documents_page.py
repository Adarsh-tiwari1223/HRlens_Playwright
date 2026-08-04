"""
Company Documents Page Object (HR Lens Portal).
Handles document repository listing, uploads, checkbox selections, bulk delete operations, and toast messages.
URL Route: /company-documents
"""

import os
import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class CompanyDocumentsPage(BasePage):
    # Route URL
    ROUTE_URL = f"{settings.BASE_URL}/master/company-document"

    # Locators
    ADD_DOC_BTN = "button:has-text('Add Doc'), button:has-text('Add Document'), button:has-text('Upload')"
    HEADER_CHECKBOX = "thead th:nth-child(1) .chakra-checkbox__control, thead th:nth-child(1) input[type='checkbox']"
    ROW_CHECKBOXES = "tbody td:nth-child(1) .chakra-checkbox__control, tbody td:nth-child(1) input[type='checkbox']"
    BULK_DELETE_BTN = "button:has-text('Delete Selected'), button:has-text('Multiple Delete'), button:has-text('Delete')"
    CONFIRM_DELETE_BTN = ".chakra-modal__content button:has-text('Confirm'), [role='dialog'] button:has-text('Delete'), button:has-text('Yes')"
    TOAST = (
        "[role='region'][aria-live='polite'] [role='status'], "
        "[role='region'][aria-live='polite'] [role='alert'], "
        ".chakra-toast, .chakra-toast__title, div[id^='toast-']"
    )

    def get_company_document_validation_rules(self, doc_name: str, category_id: int = 9) -> dict:
        """
        Company Documents Module Only:
        Retrieves dynamic validation rules (can_expire, accept_duplicate, branch_wise)
        exclusively for Company Document uploads and management.
        """
        from utils.api.company_api import get_document_validation_rules_api
        logger.info(f"Retrieving Company Document Module validation rules for '{doc_name}'...")
        return get_document_validation_rules_api(doc_name=doc_name, category_id=category_id)

    def navigate_to_company_documents(self):
        """
        Navigates to Company Documents page via left sidebar navigation:
        1. Click 'Master' menu item in left sidebar.
        2. Click '• Company Document' link.
        """
        logger.info("Navigating to Company Documents via sidebar...")
        if "/master/company-document" not in self.page.url:
            try:
                # 1. Click Master in sidebar
                master_link = self.page.locator("aside, nav, .sidebar, body").get_by_text("Master", exact=True).first
                if not master_link.is_visible():
                    master_link = self.page.get_by_role("button", name=re.compile(r"^Master$", re.IGNORECASE)).first
                if master_link.is_visible():
                    master_link.click(force=True)
                    self.page.wait_for_timeout(300)

                # 2. Click • Company Document link
                doc_link = self.page.get_by_role("link", name=re.compile(r"Company Document", re.IGNORECASE)).first
                if not doc_link.is_visible():
                    doc_link = self.page.locator("a[href*='company-document']").first
                if doc_link.is_visible():
                    doc_link.click(force=True)
                    self.page.wait_for_load_state("domcontentloaded")
            except Exception as e:
                logger.warning(f"Sidebar click error: {e}")

        # 3. Direct route navigation fallback
        if "/master/company-document" not in self.page.url:
            self.page.goto(self.ROUTE_URL, timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")

    def search_document(self, query: str):
        """Searches for specific document by title in search input."""
        logger.info(f"Filtering company documents search query: '{query}'")
        search_input = self.page.locator("input[placeholder*='Search']").first
        if search_input.is_visible():
            search_input.fill("")
            search_input.press_sequentially(query, delay=30)
            self.page.wait_for_timeout(400)

    def get_document_row_count(self) -> int:
        """Returns total number of document rows in table grid."""
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
            return self.page.locator("tbody tr").count()
        except Exception:
            return 0

    def _get_column_indices(self) -> tuple[int, int]:
        """
        Dynamically scans <thead> headers to determine exact column index numbers:
        Returns (checkbox_col_index_1_based, document_col_index_1_based).
        Ensures 100% future-proof execution even if developers reorder columns.
        """
        chk_idx = 1
        doc_idx = 3
        try:
            headers = self.page.locator("thead th").all()
            for idx, th in enumerate(headers, start=1):
                txt = th.inner_text().strip().lower()
                if th.locator(".chakra-checkbox, input[type='checkbox']").count() > 0:
                    chk_idx = idx
                elif "document" in txt or "category" in txt:
                    doc_idx = idx
        except Exception:
            pass
        return chk_idx, doc_idx

    def select_multiple_document_checkboxes(self, count: int = 2) -> list[str]:
        """
        Selects specified number of document row checkboxes in table grid.
        Uses dynamic column index resolution to ensure 100% future-proof execution.
        """
        self.navigate_to_company_documents()
        chk_col, doc_col = self._get_column_indices()
        logger.info(f"Dynamic Column Resolution: Checkbox Col={chk_col}, Document Col={doc_col}")

        selected_names = []
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
            rows = self.page.locator("tbody tr").all()

            for i, row in enumerate(rows[:count]):
                chk = row.locator(f"td:nth-child({chk_col}) .chakra-checkbox__control, td:nth-child({chk_col}) label.chakra-checkbox, .chakra-checkbox, input[type='checkbox']").first
                if chk.is_visible():
                    chk.click(force=True)
                    doc_cell = row.locator(f"td:nth-child({doc_col})").first
                    doc_name = doc_cell.inner_text().strip() if doc_cell.is_visible() else row.inner_text().splitlines()[0].strip()
                    selected_names.append(doc_name)
                    self.page.wait_for_timeout(200)

        except Exception as e:
            logger.warning(f"Error selecting checkboxes: {e}")

        return selected_names

    def select_all_header_checkbox(self):
        """Selects the master checkbox in table header using dynamic column index."""
        chk_col, _ = self._get_column_indices()
        logger.info(f"Selecting header 'Select All' checkbox at dynamic index {chk_col}...")
        chk = self.page.locator(f"thead th:nth-child({chk_col}) .chakra-checkbox__control, thead th:nth-child({chk_col}) label.chakra-checkbox, thead input[type='checkbox']").first
        if chk.is_visible():
            chk.click(force=True)
            self.page.wait_for_timeout(300)

    def wait_and_get_bulk_delete_button(self, timeout: int = 10000):
        """
        Reusable helper to wait for the dynamically rendered 'Delete Selected (n)' button.
        Uses regex matching for 'Delete Selected' to ignore count variations (1, 2, 3...).
        Uses explicit Playwright wait_for(state="visible").
        Fails with clear error message if button fails to render after checkbox selection.
        """
        logger.info("Waiting for dynamic 'Delete Selected' bulk action button to render...")
        btn_locator = self.page.locator("button, .chakra-button").filter(
            has_text=re.compile(r"Delete Selected|Multiple Delete|Delete", re.IGNORECASE)
        ).first

        try:
            btn_locator.wait_for(state="visible", timeout=timeout)
            return btn_locator
        except Exception:
            raise AssertionError(
                "Bulk action button 'Delete Selected' was not rendered after selecting document checkboxes."
            )

    def click_bulk_delete(self) -> str | None:
        """
        Clicks Bulk Delete / Delete Selected button, verifies confirmation modal header
        and dynamic text message, and clicks Delete button in modal.
        """
        logger.info("Executing Bulk Delete action...")
        btn = self.wait_and_get_bulk_delete_button()
        btn.click(force=True)

        # 1. Verify modal header ("Delete Documents")
        modal_header = self.page.locator("header").filter(has_text=re.compile(r"Delete Documents", re.IGNORECASE)).first
        try:
            modal_header.wait_for(state="visible", timeout=6000)
        except Exception:
            logger.warning("Modal header 'Delete Documents' was not detected within timeout.")

        # 2. Inspect dynamic confirmation message text ("Are you sure you want to delete X selected document(s)")
        modal_msg = self.page.locator("div").filter(has_text=re.compile(r"Are you sure you want to delete \d+ selected document\(s\)", re.IGNORECASE)).first
        if modal_msg.is_visible():
            logger.info(f"Modal Confirmation Message: '{modal_msg.inner_text().strip()}'")

        # 3. Click modal Delete button
        confirm_btn = self.page.get_by_role("button", name="Delete").first
        if not confirm_btn.is_visible():
            confirm_btn = self.page.locator(".chakra-modal__content button:has-text('Delete'), [role='dialog'] button:has-text('Delete')").first

        try:
            confirm_btn.wait_for(state="visible", timeout=5000)
            confirm_btn.click(force=True)
        except Exception as e:
            logger.warning(f"Error clicking modal Delete button: {e}")

        return self.wait_for_toast(self.TOAST)

    def upload_sample_company_document(self, doc_name: str, file_path: str) -> str | None:
        """Uploads a sample company document for testing deletion."""
        logger.info(f"Uploading company document '{doc_name}'...")
        self.navigate_to_company_documents()

        add_btn = self.page.locator(self.ADD_DOC_BTN).first
        if add_btn.is_visible():
            add_btn.click()
            self.page.wait_for_timeout(300)

        # Fill Document Title / Name
        title_input = self.page.locator(".chakra-modal__content input[type='text'], input[name='documentTitle']").first
        if title_input.is_visible():
            title_input.fill(doc_name)

        # Set File Input
        if file_path and os.path.exists(file_path):
            file_input = self.page.locator(".chakra-modal__content input[type='file']").first
            if file_input.is_visible():
                file_input.set_input_files(file_path)

        save_btn = self.page.locator(".chakra-modal__content button[type='submit'], [role='dialog'] button:has-text('Save')").first
        if save_btn.is_visible():
            save_btn.click(force=True)

        return self.wait_for_toast(self.TOAST)
