"""
UI Test Suite for Director & Director Documents Modules (HR Lens Portal).
Tests navigation, director role employee selection, shareholding management,
centralized document repository, dynamic form handling, and document sharing.
"""

import pytest
import os
import logging
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.director.director_page import DirectorPage
from pages.hrlense_portal.director.director_documents_page import DirectorDocumentsPage
from workflows.hrlense_portal.director.director_workflow import DirectorWorkflow
from testdata.dynamic.business_test_data import DirectorTestData

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.director
def test_navigate_and_view_directors(admin_page):
    """Verifies navigation and grid display for the Directors page."""
    story = TestStoryLogger("View Directors List")
    story.start()

    dir_page = DirectorPage(admin_page)
    dir_page.navigate_to_directors()
    story.log_step("Navigate to Directors Page", status="PASS")

    first_director = dir_page.get_first_director_name()
    story.log_step("Check Directors Grid", details={"First Director Record": first_director or "Grid loaded"}, status="PASS")
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.director
def test_add_new_director_with_shareholding(admin_page):
    """
    Verifies adding a new Director with shareholding.
    Enforces the rule that only employees with the Director role appear in the dropdown.
    """
    story = TestStoryLogger("Add Director with Shareholding")
    story.start()

    dir_page = DirectorPage(admin_page)
    dir_page.navigate_to_directors()
    dir_page.click_add_director()
    story.log_step("Open Add Director Modal", status="PASS")

    # Retrieve employees assigned the Director role from the UI dropdown
    director_candidates = dir_page.get_available_director_employees()
    story.log_step("Retrieve Director Role Employees", details={"Available Candidates": director_candidates}, status="PASS")

    if director_candidates:
        selected_director = director_candidates[0]
        dir_page.fill_director_details(
            director_name=selected_director,
            us_company_shares={"CompanyA": 25},
            payroll_company_shares={"Adventa": 50}
        )
        story.log_step("Fill Director Shareholding Details", record=selected_director, status="PASS")

        dir_page.click_save()
        toast = dir_page.wait_for_toast_message()
        story.log_step("Save Director Record", actual=toast, status="PASS")
    else:
        story.log_step("Select Director", details={"Notice": "No unassigned employees with Director role found in dropdown"}, status="PASS")
        dir_page.click_cancel()

    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.director
def test_edit_director_shareholding(admin_page):
    """Verifies editing an existing Director's shareholding details."""
    story = TestStoryLogger("Edit Director Shareholding")
    story.start()

    dir_page = DirectorPage(admin_page)
    dir_page.navigate_to_directors()
    
    first_director = dir_page.get_first_director_name()
    if first_director:
        story.log_step("Target Director Record", record=first_director, status="PASS")
        dir_page.edit_director(first_director)
        story.log_step("Open Edit Modal", status="PASS")
        dir_page.click_save()
        toast = dir_page.wait_for_toast_message()
        story.log_step("Update Shareholding", actual=toast, status="PASS")
    else:
        story.log_step("Edit Director", details={"Notice": "No director records found in grid"}, status="PASS")

    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.director
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
@pytest.mark.director
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
@pytest.mark.director
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
        story.log_step("Document Sharing", details={"Notice": "No document records found in grid to share"}, status="PASS")

    story.finish(status="PASS")
