"""
Company Documents Workflow Layer (HR Lens Portal).
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Encapsulates bulk document selection, multi-delete execution, and verification.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.master.company_documents_page import CompanyDocumentsPage
from utils.logger import log_step, log_debug

logger = logging.getLogger(__name__)


class CompanyDocumentsWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.docs_page = CompanyDocumentsPage(page)

    def refresh_page(self):
        """Reloads page to ensure clean UI state."""
        try:
            self.page.reload()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def bulk_delete_company_documents_workflow(self, delete_count: int = 2) -> tuple[int, int, list[str], str]:
        """
        Executes Bulk Delete / Multiple Delete workflow on Company Documents repository:
        1. Navigates to /master/company-document.
        2. Measures initial row count.
        3. Selects multiple document row checkboxes.
        4. Clicks Bulk Delete and confirms modal dialog.
        Returns (initial_count, post_delete_count, selected_names, toast_message).
        """
        log_step("Company Documents Workflow: Bulk Delete Execution", value=f"Count={delete_count}")
        self.docs_page.navigate_to_company_documents()

        initial_count = self.docs_page.get_document_row_count()
        log_debug(f"Total documents before bulk deletion: {initial_count}")

        if initial_count == 0:
            log_debug("Document repository is empty; uploading sample test documents...")
            pdf_sample = "testdata/static/pdf/sample-pdf-file-100kb.pdf"
            for k in range(1, delete_count + 1):
                self.docs_page.upload_sample_company_document(f"Sample Test Document {k}", pdf_sample)
                self.page.wait_for_timeout(400)
            self.refresh_page()
            self.docs_page.navigate_to_company_documents()
            initial_count = self.docs_page.get_document_row_count()

        selected_names = self.docs_page.select_multiple_document_checkboxes(count=delete_count)
        log_step("Selected Documents for Bulk Delete", value=", ".join(selected_names))

        toast = self.docs_page.click_bulk_delete()
        log_step("Bulk Delete Toast Notification", value=toast)

        self.refresh_page()
        self.docs_page.navigate_to_company_documents()
        post_count = self.docs_page.get_document_row_count()
        log_debug(f"Total documents after bulk deletion: {post_count}")

        return initial_count, post_count, selected_names, toast or ""

    def verify_documents_deleted(self, toast_msg: str) -> bool:
        """
        Verifies bulk deletion by checking successful toast notification response from backend API.
        """
        log_step("Verify Bulk Deletion Result", value=toast_msg)
        return bool(toast_msg and ("success" in toast_msg.lower() or "deleted" in toast_msg.lower() or "removed" in toast_msg.lower()))
