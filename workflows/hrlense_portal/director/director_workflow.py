"""
Director Module Workflow Layer for HR Lens Portal.
Encapsulates complete business workflows for Director management and Director KYC Documents.
"""

import logging
from playwright.sync_api import Page
from pages.hrlense_portal.director.director_page import DirectorPage
from pages.hrlense_portal.director.director_documents_page import DirectorDocumentsPage

logger = logging.getLogger(__name__)


class DirectorWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.director_page = DirectorPage(page)
        self.director_docs_page = DirectorDocumentsPage(page)

    def create_director_workflow(self, director_name: str, us_shares: dict = None, payroll_shares: dict = None):
        """Workflow to navigate to Directors page and add a new Director shareholding record."""
        logger.info(f"[WORKFLOW] Adding Director: {director_name}")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()
        self.director_page.fill_director_details(
            director_name=director_name,
            us_company_shares=us_shares,
            payroll_company_shares=payroll_shares
        )
        self.director_page.click_save()

    def edit_director_workflow(self, director_name: str):
        """Workflow to edit an existing Director record."""
        logger.info(f"[WORKFLOW] Editing Director: {director_name}")
        self.director_page.navigate_to_directors()
        self.director_page.edit_director(director_name)
        self.director_page.click_save()

    def add_director_document_workflow(self, doc_type: str, doc_number: str, file_path: str = None, director_name: str = None):
        """Workflow to upload a new KYC document for a director."""
        logger.info(f"[WORKFLOW] Uploading KYC Document '{doc_type}' ({doc_number}) for Director '{director_name}'")
        self.director_docs_page.navigate_to_director_documents()
        self.director_docs_page.click_add_document()
        self.director_docs_page.fill_document_form(
            doc_type=doc_type,
            doc_number=doc_number,
            file_path=file_path,
            director_name=director_name
        )
        self.director_docs_page.click_save_document()

    def share_document_internally_workflow(self, doc_number: str, employee_name: str, permission: str = "View Only"):
        """Workflow to internally share a director document with an employee."""
        logger.info(f"[WORKFLOW] Sharing document '{doc_number}' with '{employee_name}'")
        self.director_docs_page.navigate_to_director_documents()
        self.director_docs_page.share_document_internal(doc_number, employee_name, permission)
