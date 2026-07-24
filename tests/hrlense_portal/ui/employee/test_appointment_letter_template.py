import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.hrlense_portal.employee.appointment_letter_template_page import AppointmentLetterTemplatePage
from testdata.static.appointment_letter_sections import APPOINTMENT_LETTER_SECTIONS

# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def template_page(template_company, page):
    """Login as admin and navigate to the Appointment Letter Template page for the target company."""
    company_name = template_company
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")

    tp = AppointmentLetterTemplatePage(page)
    tp.navigate_to_appointment_letter_template()
    tp.select_company(company_name)
    
    print(f"\n[FIXTURE] Active Company Context: {company_name}")
    return tp

# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.ui
@pytest.mark.template
def test_create_appointment_letter_section(template_page):
    """
    Test 1: Create Appointment Letter Section with all required fields 
    (Section Key, Title, Content, Style, Order).
    """
    target_section = APPOINTMENT_LETTER_SECTIONS[0]
    template_page.add_section(target_section, start_order=target_section["order"])
    template_page.read_section(target_section["key"])


@pytest.mark.ui
@pytest.mark.template
def test_update_section_details(template_page):
    """
    Test 2: Update section details (Coverage: Title, Content, Order).
    """
    target_section = APPOINTMENT_LETTER_SECTIONS[0]
    new_title = target_section["title"] + " Updated"
    new_content = target_section["content"] + " Updated Content."
    
    template_page.update_section(
        section_key=target_section["key"],
        new_title=new_title,
        new_content=new_content,
        enforce_order=target_section["order"]
    )
    
    # Restore original for subsequent tests
    template_page.update_section(
        section_key=target_section["key"],
        new_title=target_section["title"],
        new_content=target_section["content"]
    )


@pytest.mark.ui
@pytest.mark.template
def test_verify_active_inactive_toggle(template_page):
    """
    Test 3: Verify Active/Inactive toggle functionality.
    """
    target_section = APPOINTMENT_LETTER_SECTIONS[0]
    
    # Toggle Inactive
    template_page.toggle_section_status(target_section["key"])
    
    # Toggle Active
    template_page.toggle_section_status(target_section["key"])


@pytest.mark.ui
@pytest.mark.template
def test_create_duplicate_section_active(template_page):
    """
    Test 4: Create duplicate section when existing section is Active.
    """
    target_section = APPOINTMENT_LETTER_SECTIONS[0]
    
    # Attempt to create duplicate and assert the error toast appears
    template_page.verify_duplicate_blocked(target_section)


@pytest.mark.ui
@pytest.mark.template
def test_create_duplicate_section_inactive(template_page):
    """
    Test 5: Create duplicate section when existing section is Inactive.
    """
    target_section = APPOINTMENT_LETTER_SECTIONS[0]
    
    # Deactivate the section
    template_page.toggle_section_status(target_section["key"])
    
    try:
        # Attempt to create duplicate while inactive
        template_page.verify_duplicate_blocked(target_section)
    finally:
        # Restore active status
        template_page.toggle_section_status(target_section["key"])


@pytest.mark.ui
@pytest.mark.template
def test_verify_section_order_persistence(template_page):
    """
    Test 6: Verify section order persistence after update.
    """
    target_section = APPOINTMENT_LETTER_SECTIONS[0]
    original_order = target_section["order"]
    temp_order = 99
    
    # Update order
    template_page.update_section(
        section_key=target_section["key"],
        enforce_order=temp_order
    )
    
    # Verify order persisted
    orders = template_page.get_current_orders()
    assert orders.get(target_section["key"]) == temp_order, "Order did not persist after update."
    
    # Restore original order
    template_page.update_section(
        section_key=target_section["key"],
        enforce_order=original_order
    )


@pytest.mark.ui
@pytest.mark.template
def test_seed_all_sections_for_all_companies(template_page):
    """
    Test 7: Loop through all companies and create all sections (including Custom if it exists).
    This leverages the `template_page` fixture which runs this test once for every company selected.
    """
    template_page.add_all_sections()
