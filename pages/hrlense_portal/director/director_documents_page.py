"""
Director Documents Page Object for HR Lens Portal Director Module.
Handles document repository listing, uploads, dynamic document type forms,
filtering, and document sharing (Internal and External).
"""

import re
import logging
from core.config import settings
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DirectorDocumentsPage(BasePage):
    # Sidebar & navigation
    DOCUMENTS_SIDEBAR_LINK = "role=link[name=\"Director's Documents\"]"
    
    # Header actions & filters
    ADD_DOCUMENT_BTN = "role=button[name='Add Document']"
    DIRECTOR_FILTER = "internal:placeholder='Filter by Director'"
    COMPANY_FILTER = "internal:placeholder='Filter by Company'"
    PAYROLL_FILTER = "internal:placeholder='Filter by Payroll Company'"
    
    # Table selectors
    TABLE_ROWS = "tbody tr"
    
    # Modal dialog
    MODAL_DIALOG = ".chakra-modal__content, section.chakra-modal__content"
    SAVE_BTN = "role=button[name='Save']"
    SUBMIT_BTN = "role=button[name='Submit']"
    CANCEL_BTN = "role=button[name='Cancel']"
    
    # Sharing modal tabs
    INTERNAL_TAB = "role=tab[name='Internal']"
    EXTERNAL_TAB = "role=tab[name='External']"
    GENERATE_LINK_BTN = "role=button[name*='Generate Link']"
    SHARE_SUBMIT_BTN = "role=button[name*='Share']"

    # Toast notification
    TOAST = (
        "[role='region'][aria-live='polite'] [role='status'], "
        "[role='region'][aria-live='polite'] [role='alert'], "
        ".chakra-toast, .chakra-toast__title, [role='status']"
    )

    def navigate_to_director_documents(self):
        """Navigates to the centralized Director Documents repository."""
        logger.info("Navigating to Director's Documents page...")
        link = self.page.locator("a:has-text('Director')").filter(has_text="Documents").first
        if link.is_visible():
            link.click()
            self.page.wait_for_load_state("domcontentloaded")
        elif "/director-documents" not in self.page.url:
            self.page.goto(f"{settings.BASE_URL}/director-documents")
            self.page.wait_for_load_state("domcontentloaded")
            
        try:
            self.page.locator(self.TABLE_ROWS).first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

    def click_add_document(self):
        """Opens the Add Document modal."""
        logger.info("Opening Add Document modal...")
        add_btn = self.page.locator("a:has-text('Add Document'), button:has-text('Add Document')").first
        add_btn.click(force=True)
        self.page.locator(self.MODAL_DIALOG).first.wait_for(state="visible", timeout=10000)

    def fill_document_form(self, doc_type: str, doc_number: str, issue_date: str = None, expiry_date: str = None, file_path: str = None, director_name: str = None):
        """
        Fills the document upload form dynamically based on doc_type (PAN, Aadhaar, Passport, Address Proof, etc.).
        """
        logger.info(f"Filling Document Form for type '{doc_type}', number '{doc_number}'")
        
        # 1. Select Director if required
        if director_name:
            dir_input = self.page.get_by_placeholder("Select Director", exact=False)
            if dir_input.is_visible():
                dir_input.click()
                dir_input.fill(director_name)
                self.page.wait_for_timeout(500)
                self.page.locator(".chakra-portal").get_by_text(director_name, exact=False).first.click()

        # 2. Select Document Type
        type_select = self.page.get_by_placeholder("Document Type", exact=False)
        if type_select.is_visible():
            type_select.click()
            self.page.wait_for_timeout(500)
            self.page.locator(".chakra-portal").get_by_text(doc_type, exact=False).first.click()
        else:
            select_elem = self.page.locator("[role='dialog'] select[name*='type']").first
            if select_elem.is_visible():
                select_elem.select_option(label=doc_type)

        self.page.wait_for_timeout(500)

        # 3. Fill Document Number dynamically based on type
        num_placeholder = "Document Number"
        if doc_type.upper() == "PAN":
            num_placeholder = "PAN Number"
        elif doc_type.upper() == "AADHAAR":
            num_placeholder = "Aadhaar Number"
        elif doc_type.upper() == "PASSPORT":
            num_placeholder = "Passport Number"

        num_input = self.page.get_by_placeholder(num_placeholder, exact=False)
        if not num_input.is_visible():
            num_input = self.page.get_by_placeholder("Document Number", exact=False)
        if not num_input.is_visible():
            num_input = self.page.locator("[role='dialog'] input[type='text']").first
        num_input.fill(doc_number)

        # 4. Fill Issue Date if applicable
        if issue_date:
            issue_input = self.page.get_by_placeholder("Issue Date", exact=False)
            if issue_input.is_visible():
                issue_input.fill(issue_date)

        # 5. Fill Expiry Date if applicable
        if expiry_date:
            exp_input = self.page.get_by_placeholder("Expiry Date", exact=False)
            if exp_input.is_visible():
                exp_input.fill(expiry_date)

        # 6. Upload file if provided
        if file_path:
            file_input = self.page.locator("[role='dialog'] input[type='file']")
            file_input.set_input_files(file_path)
            self.page.wait_for_timeout(500)

    def click_save_document(self):
        """Submits the document form."""
        logger.info("Submitting Document form...")
        save_btn = self.page.get_by_role("button", name="Save", exact=False)
        if not save_btn.is_visible():
            save_btn = self.page.get_by_role("button", name="Submit", exact=False)
        save_btn.click()

    def click_cancel(self):
        """Cancels modal dialog."""
        logger.info("Cancelling Document modal...")
        cancel_btn = self.page.get_by_role("button", name="Cancel", exact=True)
        if cancel_btn.is_visible():
            cancel_btn.click()

    def filter_by_director(self, director_name: str):
        """Filters the document repository list by director name."""
        logger.info(f"Filtering Director Documents by Director: {director_name}")
        filter_input = self.page.get_by_placeholder("Filter by Director", exact=False)
        if filter_input.is_visible():
            filter_input.fill(director_name)
            self.page.wait_for_timeout(500)

    def _click_row_action(self, row, action_name: str, fallback_index: int = 0):
        """Helper to reliably click an action button/link inside a table row."""
        try:
            elem = row.get_by_text(action_name, exact=False).first
            if elem.is_visible():
                elem.click()
                return
        except Exception:
            pass
        action_elems = row.locator("td").locator("button, a, svg, div")
        if action_elems.count() > fallback_index:
            action_elems.nth(fallback_index).click()
        else:
            row.get_by_label(action_name, exact=False).first.click()

    def share_document_internal(self, doc_number: str, employee_name: str, permission: str = "View Only"):
        """Performs internal document sharing with an employee."""
        logger.info(f"Sharing document '{doc_number}' internally with '{employee_name}' (Perm: {permission})")
        row = self.page.locator("tbody tr").filter(has_text=doc_number).first
        self._click_row_action(row, "Share", fallback_index=2)
        self.page.locator(self.MODAL_DIALOG).wait_for(state="visible", timeout=10000)

        # Click Internal Tab
        int_tab = self.page.get_by_role("tab", name="Internal", exact=False)
        if int_tab.is_visible():
            int_tab.click()

        # Search employee
        emp_input = self.page.get_by_placeholder("Search people", exact=False)
        if not emp_input.is_visible():
            emp_input = self.page.get_by_placeholder("Add People", exact=False)
        if emp_input.is_visible():
            emp_input.fill(employee_name)
            self.page.wait_for_timeout(500)
            self.page.locator(".chakra-portal").get_by_text(employee_name, exact=False).first.click()

        # Select Permission
        perm_select = self.page.get_by_placeholder("Permission", exact=False)
        if perm_select.is_visible():
            perm_select.click()
            self.page.locator(".chakra-portal").get_by_text(permission, exact=False).first.click()

        # Click Share
        share_btn = self.page.get_by_role("button", name="Share", exact=False)
        if not share_btn.is_visible():
            share_btn = self.page.get_by_text("Share", exact=False).first
        share_btn.click()

    def share_document_external(self, doc_number: str, view_perm: bool = True, download_perm: bool = False):
        """Generates an external public sharing link for a document."""
        logger.info(f"Sharing document '{doc_number}' externally...")
        row = self.page.locator("tbody tr").filter(has_text=doc_number).first
        self._click_row_action(row, "Share", fallback_index=2)
        self.page.locator(self.MODAL_DIALOG).wait_for(state="visible", timeout=10000)

        # Click External Tab
        ext_tab = self.page.get_by_role("tab", name="External", exact=False)
        if ext_tab.is_visible():
            ext_tab.click()

        # Click Generate Link
        gen_btn = self.page.get_by_role("button", name="Generate Link", exact=False)
        if not gen_btn.is_visible():
            gen_btn = self.page.get_by_text("Generate Link", exact=False).first
        gen_btn.click()

    def click_view_document(self, doc_number: str):
        """Clicks the View icon to open document preview."""
        logger.info(f"Viewing document: {doc_number}")
        row = self.page.locator("tbody tr").filter(has_text=doc_number).first
        self._click_row_action(row, "View", fallback_index=0)

    def click_download_document(self, doc_number: str):
        """Clicks the Download icon for a document."""
        logger.info(f"Downloading document: {doc_number}")
        row = self.page.locator("tbody tr").filter(has_text=doc_number).first
        self._click_row_action(row, "Download", fallback_index=1)

    def get_first_document_number(self) -> str | None:
        """Retrieves the Document Number from the first row in the grid."""
        try:
            self.page.locator(self.TABLE_ROWS).first.wait_for(state="visible", timeout=6000)
            first_row = self.page.locator(self.TABLE_ROWS).first
            cells = first_row.locator("td").all()
            if len(cells) > 3:
                return cells[3].inner_text().strip()
        except Exception:
            pass
        return None

    def wait_for_toast_message(self) -> str:
        """Waits for and returns toast notification message."""
        return self.wait_for_toast(self.TOAST)
