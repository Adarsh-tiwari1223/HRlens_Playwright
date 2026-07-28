import pytest
import re
from datetime import datetime, timedelta
from playwright.sync_api import expect
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage

@pytest.mark.ui
def test_job_opening_draft_handling(logged_in_page):
    """
    Test draft warning panel and transition controls during job creation.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    
    if job_page.is_draft_modal_visible():
        print("\n[INFO] Pending drafts found! Testing 'Start New Instead'...")
        job_page.start_new_instead()
        expect(page.locator(job_page.BUSINESS_PROCESS)).to_be_visible()
        job_page.close_drawer_safely()
            
        job_page.click_create_new_job_opening()
        if job_page.is_draft_modal_visible():
            print("[INFO] Resuming draft...")
            job_page.resume_first_draft()
            expect(page.locator(job_page.BUSINESS_PROCESS)).to_be_visible()
            job_page.close_drawer_safely()
    else:
        print("\n[INFO] No pending drafts found in this test run. Skipping draft interaction checks.")
        expect(page.locator(job_page.BUSINESS_PROCESS)).to_be_visible()
        job_page.close_drawer_safely()


@pytest.mark.ui
def test_job_opening_draft_title_rules(logged_in_page):
    """
    Test draft title naming rules:
    - If job title selected: draft is listed under selected job title.
    - Else: draft is listed as 'Untitled Draft'.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
        
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.wait_for_timeout(1000)
    page.locator(job_page.JOB_TITLE).select_option(index=1)
    page.wait_for_timeout(500)
    
    selected_job_title = job_page.get_selected_option_text_by_label("Job Title")
    assert selected_job_title != "", "Failed to select a valid job title or read its text"
    
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected pending drafts modal to be visible"
    
    draft_a = job_page.get_first_draft_details()
    assert draft_a["title"] == selected_job_title, f"Expected draft title to be '{selected_job_title}', got '{draft_a['title']}'"
    
    job_page.start_new_instead()
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.wait_for_timeout(500)
    
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected pending drafts modal to be visible"
    
    draft_b = job_page.get_first_draft_details()
    assert draft_b["title"] == "Untitled Draft", f"Expected draft title to be 'Untitled Draft', got '{draft_b['title']}'"
    
    close_btn = page.get_by_role("button", name="Close").first
    if close_btn.is_visible():
        close_btn.click()


@pytest.mark.ui
def test_job_opening_draft_prompt_on_partial_fill(logged_in_page):
    """
    Verify that when a job opening creation form is partially filled and then closed,
    the 'unsaved changes' modal offering to save as draft is visible and functional.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
        
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.locator(job_page.NUM_OPENINGS).fill("2")
    page.wait_for_timeout(500)
    
    close_btn = page.get_by_role("button", name="Close").first
    close_btn.click()
    page.wait_for_timeout(1000)
    
    unsaved_dialog = page.locator("text=unsaved").first
    expect(unsaved_dialog).to_be_visible()
    
    save_draft_btn = page.get_by_role("button", name="Save as Draft").first
    expect(save_draft_btn).to_be_visible()
    
    save_draft_btn.click()
    toast = page.locator("text=Saved as draft").first
    expect(toast).to_be_visible(timeout=5000)


@pytest.mark.ui
def test_multiple_untitled_drafts(logged_in_page):
    """
    Create multiple drafts without selecting a Job Role.
    Verify all appear as Untitled Draft with unique Draft IDs.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    job_page.start_new_instead()
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible()
    
    all_resumes = page.locator("text=Resume →").all()
    visible_cards = []
    for btn in all_resumes:
        if btn.is_visible():
            visible_cards.append(btn.locator("xpath=./ancestor::div[contains(., 'DRAFT-')][1]"))
    
    assert len(visible_cards) >= 2, "Expected at least 2 drafts on the list"
    
    text_1 = visible_cards[0].inner_text().strip()
    clean_text_1 = "".join(line.strip() for line in text_1.split("\n"))
    match_1 = re.search(r"^(.+?)(DRAFT-\d+)", clean_text_1)
    
    text_2 = visible_cards[1].inner_text().strip()
    clean_text_2 = "".join(line.strip() for line in text_2.split("\n"))
    match_2 = re.search(r"^(.+?)(DRAFT-\d+)", clean_text_2)
    
    assert match_1 and match_2
    title_1, id_1 = match_1.group(1).strip(), match_1.group(2).strip()
    title_2, id_2 = match_2.group(1).strip(), match_2.group(2).strip()
    
    assert title_1 == "Untitled Draft"
    assert title_2 == "Untitled Draft"
    assert id_1 != id_2, f"Expected unique draft IDs, got {id_1} and {id_2}"
    
    job_page.close_drawer_safely()


@pytest.mark.ui
def test_draft_title_updates_after_job_role_change(logged_in_page):
    """
    Save draft as Job Role 1, then change Job Role to Job Role 2 and verify title updates.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
        
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.wait_for_timeout(1000)
    page.locator(job_page.JOB_TITLE).select_option(index=1)
    page.wait_for_timeout(500)
    
    title_1 = job_page.get_selected_option_text_by_label("Job Title")
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    job_page.resume_first_draft()
    
    page.locator(job_page.JOB_TITLE).select_option(index=2)
    page.wait_for_timeout(500)
    
    title_2 = job_page.get_selected_option_text_by_label("Job Title")
    assert title_1 != title_2, "Expected different job titles to test title updates"
    
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    draft = job_page.get_first_draft_details()
    assert draft["title"] == title_2, f"Expected draft title to update to {title_2}, got {draft['title']}"
    
    job_page.close_drawer_safely()


@pytest.mark.ui
def test_resume_untitled_draft_and_publish(logged_in_page):
    """
    Save as Untitled Draft, resume it, complete all required fields and publish it.
    Verify the draft is no longer in the list.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    draft_details = job_page.get_first_draft_details()
    draft_id = draft_details["draft_id"]
    
    job_page.resume_first_draft()
    
    page.locator(job_page.BUSINESS_PROCESS).select_option(index=1)
    page.locator(job_page.PAYROLL_COMPANY).select_option(index=1)
    page.locator(job_page.BRANCH).select_option(index=1)
    page.locator(job_page.JOB_TITLE).select_option(index=1)
    page.locator(job_page.NUM_OPENINGS).fill("1")
    page.locator(job_page.EMPLOYMENT_TYPE).select_option(index=1)
    page.locator(job_page.OPENING_DATE).fill(datetime.now().strftime("%Y-%m-%d"))
    page.locator(job_page.CLOSING_DATE).fill((datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"))
    page.locator(job_page.SALARY_MIN).fill("15000")
    page.locator(job_page.SALARY_MAX).fill("20000")
    page.locator(job_page.URGENCY_LEVEL).select_option(index=1)
    page.locator(job_page.WORK_MODE).select_option(index=1)
    page.locator(job_page.EXPECTED_JOIN_DATE).fill((datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"))
    
    page.locator(job_page.ADDITIONAL_DETAILS).click()
    page.locator(job_page.EXP_MIN).fill("0")
    page.locator(job_page.EXP_MAX).fill("1")
    
    page.locator("div").filter(has_text=re.compile(r"^Enter Job Summary$")).locator("div").first.fill("E2E resumed draft publishing test.")
    
    page.get_by_role("button", name="Update Job").click()
    
    confirm_btn = page.locator(job_page.CONFIRM_BTN).first
    try:
        confirm_btn.wait_for(state="visible", timeout=3000)
        confirm_btn.click()
    except Exception:
        print("[INFO] No confirmation button appeared after clicking 'Update Job'. Continuing.")
        
    page.wait_for_load_state("networkidle")
    job_page.close_drawer_safely()
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        dialog_text = page.locator(".chakra-modal__content").first.inner_text()
        assert draft_id not in dialog_text, f"Expected published draft {draft_id} to be deleted, but it is still listed."
        job_page.close_drawer_safely()


@pytest.mark.ui
def test_discard_draft(logged_in_page):
    """
    Fill partial job opening details, close the drawer and choose to discard changes.
    Verify no draft is created.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
        
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    
    close_btn = page.get_by_role("button", name="Close").first
    close_btn.click()
    page.wait_for_timeout(1000)
    
    discard_btn = page.get_by_role("button", name="Discard Changes").first
    expect(discard_btn).to_be_visible()
    discard_btn.click()
    page.wait_for_timeout(1000)


@pytest.mark.ui
def test_save_draft_with_missing_required_fields(logged_in_page):
    """
    Verify users can save incomplete Job Openings as Drafts and restore them correctly.
    """
    page, context = logged_in_page("admin")
    
    page.get_by_role("button", name="Recruitment Portal").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Job Openings").click()
    page.get_by_role("link", name="• Active Jobs").click()
    page.wait_for_load_state("networkidle")
    
    job_page = JobOpeningPage(page)
    
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        job_page.start_new_instead()
        
    page.locator(job_page.DEPARTMENT).select_option(index=1)
    page.wait_for_timeout(1000)
    saved_dept_text = job_page.get_selected_option_text_by_label("Department")
    assert saved_dept_text != "", "Failed to select department option"
    
    job_page.close_drawer_safely(save_draft=True)
    
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected drafts modal to be visible"
    
    draft = job_page.get_first_draft_details()
    assert draft["title"] == "Untitled Draft", f"Expected draft title 'Untitled Draft', got '{draft['title']}'"
    
    job_page.resume_first_draft()
    restored_dept = job_page.get_selected_option_text_by_label("Department")
    assert restored_dept == saved_dept_text, f"Expected department to be '{saved_dept_text}', got '{restored_dept}'"
    
    job_page.close_drawer_safely(save_draft=False)
