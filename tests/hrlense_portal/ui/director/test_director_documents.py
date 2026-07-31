"""
UI Test Suite for Director Documents Module (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Implements actual Business Rule BR-001 (Director Data Consistency Validation):
Every Director displayed in /directors table must also appear in the Director dropdown of the Add Document modal.
"""

import os
import pytest
import random
from faker import Faker
from workflows.hrlense_portal.director.director_documents_workflow import DirectorDocumentsWorkflow
from utils.logger import log_test_start, log_pass, log_skip


@pytest.fixture(autouse=True)
def refresh_ui_after_scenario(admin_page):
    """Teardown fixture ensuring clean UI state."""
    yield
    try:
        admin_page.reload()
        admin_page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass


# ==============================================================================
# 🟢 PHASE 1: DIRECTOR DATA CONSISTENCY VALIDATION (BR-001)
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.director_documents
@pytest.mark.dependency(name="test_director_dropdown_data_consistency")
def test_director_dropdown_data_consistency(admin_page):
    """
    Phase 1 (BR-001): Director Data Consistency Validation.
    Every Director present in the /directors table MUST exist in the 'Director' dropdown of the Add Document modal.
    Assertion: assert set(table_directors).issubset(set(dropdown_directors))
    Fails immediately if any Director from the table is missing in the dropdown.
    """
    log_test_start(module="Director Documents", phase="Phase 1", test="BR-001 Director Data Consistency Validation")

    workflow = DirectorDocumentsWorkflow(admin_page)
    res = workflow.validate_director_data_consistency()

    table_directors = res["table_directors"]
    dropdown_directors = res["dropdown_directors"]
    clean_table = res["clean_table"]
    clean_dropdown = res["clean_dropdown"]
    missing = res["missing_directors"]

    if not table_directors:
        log_skip("No Director records currently exist in /directors table.")
        pytest.skip("No Director records in table to validate dropdown consistency.")

    # Strict subset assertion as specified in required business rules
    assert clean_table.issubset(clean_dropdown), (
        f"BR-001 Validation Failed! Directors in table are missing from Add Document dropdown. "
        f"Missing Directors: {missing} | Table: {table_directors} | Dropdown: {dropdown_directors}"
    )

    log_pass()


# ==============================================================================
# 🔵 PHASE 2: DOCUMENT CREATION WORKFLOW
# ==============================================================================

@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.director_documents
def test_add_director_kyc_document(admin_page):
    """
    Phase 2: Document Creation Workflow.
    Selects any Director from the dropdown, checks whether the selected Director already has
    the requested Document Type, and creates a document only for valid Director + Document Type pairs.
    Skips only when no valid Director + Document Type pair can be created.
    """
    log_test_start(module="Director Documents", phase="Phase 2", test="Document Creation Workflow")

    workflow = DirectorDocumentsWorkflow(admin_page)
    target_director, doc_type = workflow.get_valid_director_and_doc_type_pair()

    if not target_director or not doc_type:
        log_skip("No valid Director + Document Type combination can be created (all exist).")
        pytest.skip("No valid Director + Document Type combination can be created.")

    # Generate dynamic document number matching official regex validations
    fake = Faker("en_IN")
    if doc_type.upper() == "PAN":
        doc_number = f"ABCDE{random.randint(1000, 9999)}F"
    elif doc_type.upper() == "PASSPORT":
        letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        doc_number = f"{letter}{random.randint(1000000, 9999999)}"
    else:
        doc_number = fake.numerify("9###########")

    # Use official static test PDF file
    sample_file = os.path.abspath("testdata/static/pdf/sample-pdf-file-100kb.pdf")

    toast = workflow.add_director_document_workflow(
        director_name=target_director,
        doc_type=doc_type,
        doc_number=doc_number,
        file_path=sample_file
    )

    assert toast and ("success" in toast.lower() or "uploaded" in toast.lower() or "added" in toast.lower() or "created" in toast.lower() or "updated" in toast.lower()), f"Document creation failed! Toast response: '{toast}'"
    assert workflow.verify_document_exists(doc_number), f"Newly created document '{doc_number}' for Director '{target_director}' should be visible in table grid"
    log_pass()
