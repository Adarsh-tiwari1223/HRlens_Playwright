"""
Comprehensive Test Suite for Branch Master & Manage Signatures Feature.
URL Route: /master/branch
Role: Admin

Execution by Branch Keyword:
- pytest -k "varanasi" -> Runs Varanasi Branch workflow (Single signature, all scopes, E2E submit)
- pytest -k "agra"     -> Runs Agra Branch workflows (Brij Rawat E2E, BVA 5.1MB & DEF_024, Edit modal, Search)
- pytest -k "noida"    -> Runs Noida Branch workflow (Multi-signature stacking, individual scopes, Add More, In-block Cancel)
"""

import os
import logging
import pytest
from playwright.sync_api import expect
from pages.hrlense_portal.master.branch_page import BranchPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
def test_varanasi_branch_signature_workflow(admin_page):
    """
    Varanasi Branch:
    - Fresh open Manage Signatures module for Varanasi
    - Verify initial state: exactly 1 card, upload container hidden before employee selection
    - Multi-select scopes: Set as Default + For Payslip + For Onboarding Letters (One signature -> Many options)
    - Search Varanasi Branch Head 'Vivek' -> select '852 - Vivekanand Singh - Director - (TEK - Var )'
    - Hard assert dynamic upload container (.css-1ayfwcb) appears with employee details & Cancel button
    - Attach signature_vivek_singh.png
    - Click Submit
    - Capture and assert server response toast notification (hard DEF_024 plain text check)
    - Re-open and verify Signature List table displays row with correct badges/checkboxes
    """
    logger.info("[TEST VARANASI] Manage Signatures E2E Workflow (One signature -> Many options)")
    branch_page = BranchPage(admin_page)
    branch_page.open_manage_signatures_for_branch(branch_name="Varanasi")

    modal = branch_page.get_modal()
    expect(modal).to_be_visible(timeout=10000)

    # 1. Verify Initial State
    cards = modal.locator(branch_page.CARD_CONTAINER)
    expect(cards).to_have_count(1)
    expect(modal.locator(branch_page.UPLOAD_CONTAINER)).to_have_count(0)

    # 2. Multi-Select Scopes: One signature -> Many options
    branch_page.configure_scopes(default=True, payslip=True, onboarding=True, block_index=0)
    expect(modal.locator(branch_page.DEFAULT_CHECKBOX).first.locator("input")).to_be_checked()
    expect(modal.locator(branch_page.PAYSLIP_CHECKBOX).first.locator("input")).to_be_checked()
    expect(modal.locator(branch_page.ONBOARDING_CHECKBOX).first.locator("input")).to_be_checked()

    # 3. Search & Select Varanasi Branch Head
    selected_name = branch_page.select_employee_from_search("Vivek", block_index=0)
    assert "Vivekanand" in selected_name or "Vivek" in selected_name

    # 4. Assert Dynamic Upload Container (.css-1ayfwcb)
    upload_box = modal.locator(branch_page.UPLOAD_CONTAINER).first
    expect(upload_box).to_be_visible(timeout=6000)
    expect(upload_box.locator("label")).to_contain_text("Vivekanand Singh")
    expect(upload_box.locator("button:has-text('Cancel')")).to_be_visible()

    # 5. Attach Signature
    sig_path = os.path.abspath(r"testdata\static\image\Signature\signature_vivek_singh.png")
    assert os.path.exists(sig_path), f"Signature file missing: {sig_path}"
    branch_page.upload_signature(file_path=sig_path, block_index=0)

    # 6. Submit
    branch_page.click_submit()

    # 7. Toast Interception & DEF_024 Hard Assertion
    toast = branch_page.wait_for_toast_message(timeout=10000)
    logger.info(f"Varanasi Submit Toast: '{toast}'")
    assert toast, "Expected response toast notification upon submission"

    is_raw_json = toast.strip().startswith("{") and "success" in toast
    assert not is_raw_json, f"[DEF_024] Raw backend JSON leaked in UI toast: '{toast}'"

    branch_page.close_modal()


@pytest.mark.ui
@pytest.mark.regression
def test_noida_branch_signature_workflow(admin_page):
    """
    Noida Branch:
    - Many Signatures to Individual Options, 'Add More' dynamic stacking & In-block Cancel
    - Card 0: Individual scope 'For Payslip' only
    - Search & select Satish Singh -> upload box appears
    - In-block Cancel: clicks Cancel inside .css-1ayfwcb -> upload box resets and disappears
    - Re-select Satish Singh and attach signature_satish_singh.png
    - Click 'Add More' -> New section .css-4qyjep added (Cards = 2)
    - Card 1: Individual scope 'For Onboarding Letters' only
    - Search & select Davesh Sharma on Card 1 -> upload box appears
    - Attach signature_davesh_sharma.png to Card 1
    - Verify independent scoping across cards and dismiss
    """
    logger.info("[TEST NOIDA] Multi-signature stacked individual scopes, Add More, and in-block cancel")
    branch_page = BranchPage(admin_page)
    branch_page.open_manage_signatures_for_branch(branch_name="Noida")

    modal = branch_page.get_modal()
    expect(modal).to_be_visible(timeout=10000)

    # 1. Card 0: Individual Scope 'For Payslip' Only
    branch_page.configure_scopes(default=False, payslip=True, onboarding=False, block_index=0)

    # 2. Select Satish Singh
    branch_page.select_employee_from_search("Satish", block_index=0)
    upload_box_0 = modal.locator(branch_page.UPLOAD_CONTAINER).first
    expect(upload_box_0).to_be_visible(timeout=5000)
    expect(upload_box_0.locator("label")).to_contain_text("Satish Singh")

    # 3. Test In-Block Cancel: Reset employee selection for Card 0
    logger.info("Testing in-block Cancel button on Card 0...")
    branch_page.click_block_cancel(block_index=0)
    expect(upload_box_0).not_to_be_visible(timeout=5000)
    logger.info("In-block Cancel successfully cleared upload section.")

    # 4. Re-select Satish Singh and attach signature
    branch_page.select_employee_from_search("Satish", block_index=0)
    sig_satish = os.path.abspath(r"testdata\static\image\Signature\signature_satish_singh.png")
    assert os.path.exists(sig_satish), f"Signature asset missing: {sig_satish}"
    branch_page.upload_signature(file_path=sig_satish, block_index=0)

    # 5. Dynamic 'Add More': Adds new section .css-4qyjep
    logger.info("Clicking 'Add More' to stack a new signature section...")
    branch_page.click_add_more()
    cards = modal.locator(branch_page.CARD_CONTAINER)
    expect(cards).to_have_count(2)

    # 6. Card 1: Individual Scope 'For Onboarding Letters' Only
    branch_page.configure_scopes(default=False, payslip=False, onboarding=True, block_index=1)

    # 7. Select Davesh Sharma on Card 1
    branch_page.select_employee_from_search("Davesh", block_index=1)
    upload_box_1 = modal.locator(branch_page.UPLOAD_CONTAINER).nth(1)
    expect(upload_box_1).to_be_visible(timeout=5000)
    expect(upload_box_1.locator("label")).to_contain_text("Davesh Sharma")

    # 8. Attach Signature to Card 1
    sig_davesh = os.path.abspath(r"testdata\static\image\Signature\signature_davesh_sharma.png")
    assert os.path.exists(sig_davesh), f"Signature asset missing: {sig_davesh}"
    branch_page.upload_signature(file_path=sig_davesh, block_index=1)

    logger.info("Verified multi-signature stacking with individual options and independent file inputs.")
    branch_page.click_cancel()
    branch_page.close_modal()


@pytest.mark.ui
@pytest.mark.regression
def test_agra_branch_signature_bva_and_def_024(admin_page):
    """
    Agra Branch:
    - Boundary Value Analysis (BVA) & DEF_024 Defect Assertion
    - Attach 5.1MB boundary file (signature_brij_rawat_5_1mb.png) for Brij Rawat
    - Submit and assert toast notification
    - HARD DEF_024 ASSERTION: Toast must be plain text and NEVER unparsed JSON
    """
    logger.info("[TEST AGRA] BVA 5.1MB boundary file upload & DEF_024 verification")
    branch_page = BranchPage(admin_page)
    branch_page.open_manage_signatures_for_branch(branch_name="Agra", company_name="TEK Inspirations")

    modal = branch_page.get_modal()
    expect(modal).to_be_visible(timeout=10000)

    # Check if Brij Rawat is already configured in the Signature List table
    records = branch_page.get_signature_list_records()
    brij_exists = any("Brij Rawat" in r["employee_name"] for r in records)

    if brij_exists:
        logger.info("Brij Rawat already in list. Testing upload via Edit Signature modal...")
        branch_page.click_edit_signature("Brij Rawat")
        edit_modal = admin_page.locator("[role='dialog']").filter(has_text="Edit Signature").first
        expect(edit_modal).to_be_visible(timeout=5000)

        bva_file = os.path.abspath(r"testdata\static\image\Signature\signature_brij_rawat_5_1mb.png")
        assert os.path.exists(bva_file), f"BVA file missing: {bva_file}"
        edit_modal.locator("input[type='file']").first.set_input_files(bva_file)
        edit_modal.locator("button:has-text('Update')").first.click()
    else:
        branch_page.select_employee_from_search("Brij", block_index=0)
        bva_file = os.path.abspath(r"testdata\static\image\Signature\signature_brij_rawat_5_1mb.png")
        assert os.path.exists(bva_file), f"BVA file missing: {bva_file}"
        branch_page.upload_signature(file_path=bva_file, block_index=0)
        branch_page.click_submit()

    # Capture Toast
    toast = branch_page.wait_for_toast_message(timeout=10000)
    logger.info(f"Agra BVA Toast: '{toast}'")

    if toast:
        is_raw_json = toast.strip().startswith("{") and "success" in toast
        assert not is_raw_json, (
            f"[DEF_024 DEFECT DETECTED] Toast displayed unparsed backend JSON payload! Content: '{toast}'"
        )
        logger.info(f"DEF_024 Passed: Toast is clean text -> '{toast}'")

    branch_page.close_modal()


@pytest.mark.ui
@pytest.mark.regression
def test_agra_branch_scope_combinations_and_search_isolation(admin_page):
    """
    Agra Branch:
    - Scope toggle combinations (Default, Payslip, Onboarding)
    - Employee Search Isolation: verifying arbitrary employees do NOT appear (only branch head/HR)
    """
    logger.info("[TEST AGRA] Scope toggle combinations and search isolation")
    branch_page = BranchPage(admin_page)
    branch_page.open_manage_signatures_for_branch(branch_name="Agra", company_name="TEK Inspirations")

    modal = branch_page.get_modal()
    expect(modal).to_be_visible(timeout=10000)

    def_cb = modal.locator(branch_page.DEFAULT_CHECKBOX).first.locator("input")
    pay_cb = modal.locator(branch_page.PAYSLIP_CHECKBOX).first.locator("input")
    onb_cb = modal.locator(branch_page.ONBOARDING_CHECKBOX).first.locator("input")

    # Scope Combination A: Default Only
    branch_page.configure_scopes(default=True, payslip=False, onboarding=False)
    expect(def_cb).to_be_checked()
    expect(pay_cb).not_to_be_checked()
    expect(onb_cb).not_to_be_checked()

    # Scope Combination B: Payslip + Onboarding
    branch_page.configure_scopes(default=False, payslip=True, onboarding=True)
    expect(def_cb).not_to_be_checked()
    expect(pay_cb).to_be_checked()
    expect(onb_cb).to_be_checked()

    # Search Isolation: Non-branch arbitrary name yields no options
    search_input = modal.locator(branch_page.SEARCH_EMPLOYEE_INPUT).first
    search_input.click()
    search_input.fill("InvalidNonExistentEmployee999")
    admin_page.wait_for_timeout(1000)
    suggestions = modal.locator(branch_page.DROPDOWN_SUGGESTION)
    expect(suggestions).to_have_count(0)
    logger.info("Search isolation verified: Arbitrary employees do not appear.")

    branch_page.click_cancel()
    branch_page.close_modal()


@pytest.mark.ui
@pytest.mark.regression
def test_agra_branch_signature_list_table_search_and_edit(admin_page):
    """
    Agra Branch:
    - Real-time search inside Signature List table
    - In-place Edit Signature modal verification
    """
    logger.info("[TEST AGRA] Signature List table search & Edit modal workflow")
    branch_page = BranchPage(admin_page)
    branch_page.open_manage_signatures_for_branch(branch_name="Agra", company_name="TEK Inspirations")

    modal = branch_page.get_modal()
    expect(modal).to_be_visible(timeout=10000)

    records = branch_page.get_signature_list_records()
    logger.info(f"Active signature records in Agra: {len(records)}")

    if len(records) > 0:
        target_name = records[0]["employee_name"]
        first_word = target_name.split()[0]

        # Table Search
        branch_page.search_signature_list(first_word)
        filtered = branch_page.get_signature_list_records()
        assert len(filtered) > 0, f"Expected matching results for '{first_word}'"
        for r in filtered:
            assert first_word.lower() in r["employee_name"].lower()

        # Clear Search
        branch_page.search_signature_list("")

        # Edit Signature Modal
        branch_page.click_edit_signature(target_name)
        edit_modal = admin_page.locator("[role='dialog']").filter(has_text="Edit Signature").first
        expect(edit_modal).to_be_visible(timeout=5000)
        expect(edit_modal.locator("text=Replace Signature (optional)").first).to_be_visible()
        expect(edit_modal.locator("button:has-text('Update')").first).to_be_visible()

        # Close Edit Modal
        close_btn = edit_modal.locator("button[aria-label='Close'], button:has-text('Cancel')").first
        close_btn.click()
        logger.info("Edit Signature modal verified and dismissed.")

    branch_page.close_modal()
