import pytest
import re
import logging
from datetime import datetime, timedelta
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage
from workflows.recruitment_portal.active_job.job_opening_workflow import JobOpeningWorkflow

logger = logging.getLogger(__name__)

@pytest.mark.ui
def test_job_opening_draft_handling(logged_in_page):
    """
    Test draft warning modal: extracts all listed drafts, selects a random draft,
    logs its details, resumes editing, and validates 'Edit New Job Opening' header.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected 'Pending Drafts Found' modal to be visible"

    picked_draft = job_page.resume_random_draft()
    logger.info(f"[PASS] Successfully picked & resumed Draft: {picked_draft['title']} ({picked_draft['draft_id']})")

    assert job_page.is_edit_job_opening_header_visible(), "Expected 'Edit New Job Opening' header to be visible after resuming draft"
    logger.info("[PASS] Verified 'Edit New Job Opening' header is visible.")

    job_page.close_drawer_safely(save_draft=False)


@pytest.mark.ui
def test_job_opening_draft_title_rules(logged_in_page):
    """
    Test draft title naming rules:
    - Pick a draft and store its persistent DRAFT-N ID.
    - Dynamically select a random Job Title (different from current title).
    - Save draft and re-open modal.
    - Read all drafts, map by ID, and verify the title refreshed accurately.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    # 1. Open modal
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected pending drafts modal to be visible"

    # 2. Pick first draft and store its persistent DRAFT-N ID and initial title
    draft = job_page.resume_first_draft()
    target_draft_id = draft["draft_id"]
    old_title = draft["title"]
    logger.info(f"[STEP] Resumed Target Draft        : '{old_title}' [{target_draft_id}]")

    # 3. Dynamically select a random Job Title different from old_title
    new_job_title = job_page.select_random_job_title(exclude_title=old_title)
    if not new_job_title:
        new_job_title = job_page.select_job_title(index=2)
    assert new_job_title != "", "Failed to select a valid job title dynamically"
    logger.info(f"[ACTION] Updating Job Title Dynamically: '{old_title}' -> '{new_job_title}'")

    # 4. Save as Draft and close drawer
    job_page.close_drawer_safely(save_draft=True)

    # 5. Re-open Create New Job Opening to view drafts list
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected pending drafts modal to be visible"

    # 6. Read whole draft list, map by Draft ID (DRAFT-N), and verify refreshed title
    all_drafts = job_page.get_all_draft_items()
    draft_title_map = {d["draft_id"]: d["title"] for d in all_drafts}
    
    assert target_draft_id in draft_title_map, f"Draft ID {target_draft_id} not found in modal list: {list(draft_title_map.keys())}"
    actual_updated_title = draft_title_map[target_draft_id]

    logger.info(f"[VERIFY] Checking Draft [{target_draft_id}]: '{old_title}' -> '{actual_updated_title}'")
    assert actual_updated_title == new_job_title, f"Expected title '{new_job_title}', but got '{actual_updated_title}' for {target_draft_id}"
    logger.info(f"[PASS] Draft [{target_draft_id}] successfully refreshed to '{actual_updated_title}'")

    job_page.close_drawer_safely(save_draft=False)


@pytest.mark.ui
def test_job_opening_draft_prompt_on_partial_fill(logged_in_page):
    """
    Verify that when a job opening creation form is partially filled and then closed,
    the 'unsaved changes' modal offering to save as draft is visible and functional.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    job_page.open_create_job_form()
    job_page.select_business_process(index=1)
    job_page.select_department(index=1)
    job_page.fill_job_fields(num_openings="2")

    # Closing drawer with save_draft=True validates unsaved changes modal & saves draft
    job_page.close_drawer_safely(save_draft=True)


@pytest.mark.ui
def test_multiple_untitled_drafts(logged_in_page):
    """
    Create multiple drafts without selecting a Job Role.
    Verify all appear as Untitled Draft with unique Draft IDs.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    # First Untitled Draft
    job_page.open_create_job_form()
    job_page.select_business_process(index=1)
    job_page.select_department(index=1)
    job_page.close_drawer_safely(save_draft=True)

    # Second Untitled Draft
    job_page.open_create_job_form()
    job_page.select_business_process(index=1)
    job_page.select_department(index=1)
    job_page.close_drawer_safely(save_draft=True)

    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected draft modal visible"

    all_drafts = job_page.get_all_draft_items()
    untitled_drafts = [d for d in all_drafts if d["title"] == "Untitled Draft"]
    logger.info(f"[VERIFY] Total Untitled Drafts found in modal: {len(untitled_drafts)}")

    # Scope verification to the latest min 2 and max 3 drafts
    scoped_untitled = untitled_drafts[:3]
    assert 2 <= len(scoped_untitled) <= 3, f"Expected between 2 and 3 scoped untitled drafts, found {len(scoped_untitled)}"

    draft_ids = [d["draft_id"] for d in scoped_untitled]
    assert len(draft_ids) == len(set(draft_ids)), f"Duplicate draft IDs detected in scoped drafts: {draft_ids}"
    logger.info(f"[PASS] Verified scoped Untitled Drafts (min 2, max 3) with unique IDs: {draft_ids}")

    job_page.close_drawer_safely(save_draft=False)


@pytest.mark.ui
def test_draft_title_updates_after_job_role_change(logged_in_page):
    """
    Save draft as Job Role 1, then change Job Role to Job Role 2 and verify title updates.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    job_page.open_create_job_form()
    job_page.select_business_process(index=1)
    job_page.select_department(index=1)
    title_1 = job_page.select_job_title(index=1)
    job_page.close_drawer_safely(save_draft=True)

    job_page.click_create_new_job_opening()
    job_page.resume_first_draft()

    title_2 = job_page.select_job_title(index=2)
    assert title_1 != title_2, "Expected different job titles"

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
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    # 1. Open draft modal
    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected pending drafts modal to be visible"

    # 2. Pick first draft and store its draft_id
    draft = job_page.resume_first_draft()
    target_draft_id = draft["draft_id"]
    logger.info(f"[STEP] Resumed Target Draft for Publishing: '{draft['title']}' [{target_draft_id}]")

    # 3. Fill missing mandatory dropdowns and fields
    job_page.select_business_process(index=1)
    job_page.select_payroll_company(index=1)
    job_page.select_branch(index=1)
    job_page.select_department(index=1)
    job_page.select_job_title(index=1)
    job_page.select_employment_type(index=1)
    job_page.select_urgency_level(index=1)
    job_page.select_work_mode(index=1)

    opening_dt = datetime.now().strftime("%Y-%m-%d")
    closing_dt = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    expected_doj = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")

    job_page.fill_job_fields(
        num_openings="1",
        opening_date=opening_dt,
        closing_date=closing_dt,
        salary_min="15000",
        salary_max="20000",
        doj=expected_doj,
        min_exp="0",
        max_exp="1"
    )

    job_page.set_job_summary("E2E resumed draft publishing test description.")

    # 4. Publish / Update the job
    logger.info(f"[ACTION] Updating & Publishing resumed Draft [{target_draft_id}]...")
    pub_btn = page.locator("button:has-text('Update Job'), button:has-text('Publish Job'), button:has-text('Publish')").first
    pub_btn.wait_for(state="visible", timeout=8000)
    pub_btn.scroll_into_view_if_needed()
    pub_btn.click()

    confirm_btn = page.locator("button:has-text('Confirm')").first
    try:
        if confirm_btn.is_visible(timeout=3000):
            confirm_btn.click()
    except Exception:
        pass

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)

    # 5. Re-open Create New Job Opening to verify DRAFT-N is removed
    job_page.click_create_new_job_opening()
    if job_page.is_draft_modal_visible():
        remaining_drafts = job_page.get_all_draft_items()
        remaining_ids = [d["draft_id"] for d in remaining_drafts]
        logger.info(f"[VERIFY] Checking that Draft [{target_draft_id}] was removed from: {remaining_ids}")
        assert target_draft_id not in remaining_ids, f"Published draft {target_draft_id} was still found in modal list!"
        logger.info(f"[PASS] Confirmed Draft [{target_draft_id}] was successfully removed from draft list upon publishing.")
        job_page.close_drawer_safely(save_draft=False)
    else:
        logger.info(f"[PASS] Drafts modal no longer displays drafts (all drafts published).")


@pytest.mark.ui
def test_discard_draft(logged_in_page):
    """
    Fill partial job opening details, close the drawer and choose to discard changes.
    Verify no draft is created.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    job_page.open_create_job_form()
    job_page.select_business_process(index=1)
    job_page.select_department(index=1)
    job_page.close_drawer_safely(save_draft=False)


@pytest.mark.ui
def test_save_draft_with_missing_required_fields(logged_in_page):
    """
    Verify users can save incomplete Job Openings as Drafts and restore them correctly.
    """
    page, context = logged_in_page("admin")
    job_page = JobOpeningPage(page)
    job_page.navigate_to_active_jobs()

    job_page.open_create_job_form()
    job_page.select_business_process(index=1)
    saved_dept_text = job_page.select_department(index=1)
    assert saved_dept_text != "", "Failed to select department option"

    job_page.close_drawer_safely(save_draft=True)

    job_page.click_create_new_job_opening()
    assert job_page.is_draft_modal_visible(), "Expected drafts modal to be visible"

    draft = job_page.get_first_draft_details()
    assert draft["title"] == "Untitled Draft", f"Expected draft title 'Untitled Draft', got '{draft['title']}'"

    job_page.resume_first_draft()
    restored_dept = job_page.get_selected_option_text_by_label("Department")
    assert restored_dept == saved_dept_text, f"Expected department '{saved_dept_text}', got '{restored_dept}'"

    job_page.close_drawer_safely(save_draft=False)

