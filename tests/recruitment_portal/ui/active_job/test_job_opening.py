import pytest
from tests.recruitment_portal.ui.active_job import test_job_opening_creation as creation
from tests.recruitment_portal.ui.active_job import test_job_opening_validation as validation
from tests.recruitment_portal.ui.active_job import test_job_opening_drafts as drafts

# ==============================================================================
# Job Opening Creation Suite
# ==============================================================================

@pytest.mark.ui
def test_create_job_opening_manual(logged_in_page):
    """Test manual creation of a Job Opening."""
    creation.test_create_job_opening_manual(logged_in_page)


@pytest.mark.ui
def test_auto_jd_generation(logged_in_page):
    """Test AI Job Description generation and publishing."""
    creation.test_auto_jd_generation(logged_in_page)


# ==============================================================================
# Job Opening Validation Suite
# ==============================================================================

@pytest.mark.ui
def test_publish_requires_mandatory_fields(logged_in_page):
    """Verify that publishing requires all mandatory fields."""
    validation.test_publish_requires_mandatory_fields(logged_in_page)


@pytest.mark.ui
def test_required_field_data_logging(logged_in_page):
    """Fill mandatory fields, log entered values, and verify grid displays."""
    validation.test_required_field_data_logging(logged_in_page)


@pytest.mark.ui
def test_jd_summary_required_validation(logged_in_page):
    """Verify JD Summary required validation across Scenarios A, B, and C."""
    validation.test_jd_summary_required_validation(logged_in_page)


# ==============================================================================
# Job Opening Drafts Suite
# ==============================================================================

@pytest.mark.ui
def test_job_opening_draft_handling(logged_in_page):
    """Test draft warning panel and transition controls."""
    drafts.test_job_opening_draft_handling(logged_in_page)


@pytest.mark.ui
def test_job_opening_draft_title_rules(logged_in_page):
    """Test draft title naming rules (Job Title vs. Untitled Draft)."""
    drafts.test_job_opening_draft_title_rules(logged_in_page)


@pytest.mark.ui
def test_job_opening_draft_prompt_on_partial_fill(logged_in_page):
    """Verify unsaved changes modal when closing partially filled form."""
    drafts.test_job_opening_draft_prompt_on_partial_fill(logged_in_page)


@pytest.mark.ui
def test_multiple_untitled_drafts(logged_in_page):
    """Verify multiple untitled drafts display with unique IDs."""
    drafts.test_multiple_untitled_drafts(logged_in_page)


@pytest.mark.ui
def test_draft_title_updates_after_job_role_change(logged_in_page):
    """Verify draft title updates upon job role selection change."""
    drafts.test_draft_title_updates_after_job_role_change(logged_in_page)


@pytest.mark.ui
def test_resume_untitled_draft_and_publish(logged_in_page):
    """Resume untitled draft, fill remaining fields, and publish."""
    drafts.test_resume_untitled_draft_and_publish(logged_in_page)


@pytest.mark.ui
def test_discard_draft(logged_in_page):
    """Verify discarding unsaved changes creates no draft."""
    drafts.test_discard_draft(logged_in_page)


@pytest.mark.ui
def test_save_draft_with_missing_required_fields(logged_in_page):
    """Verify saving and resuming incomplete drafts."""
    drafts.test_save_draft_with_missing_required_fields(logged_in_page)
