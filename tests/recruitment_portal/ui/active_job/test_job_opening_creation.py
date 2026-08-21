import pytest
from faker import Faker
from workflows.recruitment_portal.active_job.job_opening_workflow import JobOpeningWorkflow
from pages.recruitment_portal.active_job.job_opening_page import JobOpeningPage

fake = Faker()

@pytest.mark.ui
def test_create_job_opening_manual(logged_in_page):
    """
    Test creating a new job opening using the 3-Tier Workflow Architecture.
    """
    page, context = logged_in_page("admin")
    workflow = JobOpeningWorkflow(page)

    summary_text = f"Manual Job Description Test\n\n{fake.paragraph()}"
    latest_job_id = workflow.create_manual_job_opening_workflow(summary_text)

    print(f"SUCCESS: Newly created Job ID is: {latest_job_id}")
    assert latest_job_id.startswith("JOB_POSTING-"), f"Invalid Job ID: '{latest_job_id}'"


@pytest.mark.ui
def test_auto_jd_generation(logged_in_page):
    """
    Test the 'Generate JD with AI' feature during Job Opening creation.
    """
    page, context = logged_in_page("admin")
    workflow = JobOpeningWorkflow(page)

    res = workflow.create_job_with_ai_jd_workflow()
    
    latest_job_id = res.get("job_id", "")
    summary_text = res.get("summary", "")

    print(f"Auto-generated JD summary: {summary_text[:100]}...")
    print(f"SUCCESS: Auto-generated Job ID is: {latest_job_id}")

    assert len(summary_text) > 10, "AI JD generation failed or returned empty text."
    assert latest_job_id.startswith("JOB_POSTING-"), f"Invalid Job ID created: '{latest_job_id}'"

