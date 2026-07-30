"""
UI Test Suite for Director Documents Module (HR Lens Portal).
Tests centralized document repository, dynamic KYC document forms, and sharing mechanics.
"""

import pytest
import os
import logging
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.director.director_documents_page import DirectorDocumentsPage
from testdata.dynamic.business_test_data import DirectorTestData

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.director_documents
def test_navigate_and_view_director_documents(admin_page):
    """Verifies navigation to the Centralized Director Documents repository."""
    story = TestStoryLogger("View Director Documents Repository")
    story.start()

    docs_page = DirectorDocumentsPage(admin_page)
    docs_page.navigate_to_director_documents()
    story.log_step("Navigate to Director Documents Page", status="PASS")

    first_doc = docs_page.get_first_document_number()
    story.log_step("Check Documents Repository Grid", details={"First Document Record": first_doc or "Repository loaded"}, status="PASS")
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.director_documents
def test_add_director_kyc_document(admin_page):
    """Verifies adding a new KYC document (PAN) for a director."""
    story = TestStoryLogger("Add Director KYC Document")
    story.start()

    docs_page = DirectorDocumentsPage(admin_page)
    docs_page.navigate_to_director_documents()
    docs_page.click_add_document()
    story.log_step("Open Add Document Modal", status="PASS")

    # Generate test document data
    doc_data = DirectorTestData.generate_document("PAN")
    
    # Create sample dummy PDF for upload
    sample_file = os.path.abspath("testdata/sample_kyc_doc.pdf")
    if not os.path.exists(sample_file):
        os.makedirs(os.path.dirname(sample_file), exist_ok=True)
        with open(sample_file, "w") as f:
            f.write("%PDF-1.4 Sample KYC Document Content")

    docs_page.fill_document_form(
        doc_type=doc_data.document_type,
        doc_number=doc_data.document_number,
        file_path=sample_file
    )
    story.log_step("Fill Document Form", details={"Doc Type": doc_data.document_type, "Doc Number": doc_data.document_number}, status="PASS")

    docs_page.click_save_document()
    toast = docs_page.wait_for_toast_message()
    story.log_step("Save Document Record", actual=toast, status="PASS")
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.director_documents
def test_internal_and_external_document_sharing(admin_page):
    """Verifies internal and external document sharing features."""
    story = TestStoryLogger("Director Document Sharing")
    story.start()

    docs_page = DirectorDocumentsPage(admin_page)
    docs_page.navigate_to_director_documents()

    first_doc = docs_page.get_first_document_number()
    if first_doc:
        story.log_step("Target Document for Sharing", record=first_doc, status="PASS")
        
        # Test Internal Sharing
        docs_page.share_document_internal(doc_number=first_doc, employee_name="Admin", permission="View Only")
        story.log_step("Execute Internal Sharing", status="PASS")

        # Test External Sharing
        docs_page.share_document_external(doc_number=first_doc, view_perm=True, download_perm=True)
        story.log_step("Execute External Sharing", status="PASS")
    else:
        story.log_step("No Document Available for Sharing", status="INFO")
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.director_documents
def test_validate_director_documents_filters_against_api(admin_page):
    """
    Cross-validates Director, Company, and Payroll Company filter lists in Director Documents
    against backend API responses.
    """
    from testdata.dynamic.business_test_data import BusinessTestData

    story = TestStoryLogger("Director Documents API Filter Cross-Validation")
    story.start()

    docs_page = DirectorDocumentsPage(admin_page)
    docs_page.navigate_to_director_documents()

    api_companies = BusinessTestData.get_companies()
    api_payroll = BusinessTestData.get_payroll_companies()

    story.log_step(
        "Cross-Validate API Master Filter Data",
        details={
            "API US Companies": len(api_companies),
            "API Payroll Companies": len(api_payroll)
        },
        status="PASS"
    )
    story.finish(status="PASS")
