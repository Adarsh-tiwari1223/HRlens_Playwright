from playwright.sync_api import Page, expect
import re
import logging
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class JobOpeningPage(BasePage):
    """
    Page Object Model for the Recruitment Portal -> Job Openings page.
    
    Contains strictly selectors and low-level UI interactions.
    Business workflows and multi-step processes are delegated to JobOpeningWorkflow.
    """

    # --- Selectors ---
    CREATE_JOB_BTN = "button:has-text('Create New Job Opening')"
    BUSINESS_PROCESS = "label:has-text('Business Process *')"
    PAYROLL_COMPANY = "label:has-text('Payroll Company *')"
    BRANCH = "label:has-text('Branch *')"
    DEPARTMENT = "label:has-text('Department *')"
    JOB_TITLE = "label:has-text('Job Title *')"
    NUM_OPENINGS = "[placeholder='Enter Number of Openings']"
    EMPLOYMENT_TYPE = "label:has-text('Employement Type *')"
    OPENING_DATE = "[placeholder='Select Job Opening Date']"
    CLOSING_DATE = "[placeholder='Select Job Closing Date']"
    SALARY_MIN = "[placeholder='Enter Salary Min']"
    SALARY_MAX = "[placeholder='Enter Salary Max']"
    URGENCY_LEVEL = "label:has-text('Urgency Level *')"
    WORK_MODE = "label:has-text('Work Mode *')"
    EXPECTED_JOIN_DATE = "[placeholder*='Select Expected Date of']"
    EXP_MIN = "label:has-text('Experience (in years) Min*')"
    EXP_MAX = "label:has-text('Experience (in years) Max*')"
    PUBLISH_BTN = "button:has-text('Publish Job')"
    CONFIRM_BTN = "button:has-text('Confirm')"
    ADDITIONAL_DETAILS = "text=Additional Details"

    # JD Summary - SunEditor contenteditable content area
    JD_SUMMARY_EDITOR = ".sun-editor-editable"

    # Draft Selectors
    PENDING_DRAFTS_TITLE = "text=Pending Drafts Found"
    START_NEW_INSTEAD_BTN = "button:has-text('Start New Instead')"
    EDIT_NEW_JOB_OPENING_BTN = "text=Edit New Job Opening"
    RESUME_DRAFT_TEXT = "text=Resume →"

    # --- Atomic UI Interactions ---

    def click_create_new_job_opening(self):
        """Clicks the 'Create New Job Opening' button."""
        self.page.locator(self.CREATE_JOB_BTN).click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def is_draft_modal_visible(self) -> bool:
        """Returns True if the 'Pending Drafts Found' panel is visible."""
        return self.check_draft_modal_or_form() == "draft"

    def check_draft_modal_or_form(self) -> str:
        """
        Waits for either the draft modal or the creation form to be visible.
        Returns 'draft' if draft modal is visible, 'form' if creation form is visible, or 'none' if neither.
        """
        for _ in range(30):
            if self.page.locator(self.PENDING_DRAFTS_TITLE).first.is_visible():
                return "draft"
            if self.page.locator(self.BUSINESS_PROCESS).first.is_visible():
                return "form"
            self.page.wait_for_timeout(100)
        return "none"

    def start_new_instead(self):
        """Clicks the 'Start New Instead' button if visible."""
        start_new_btn = self.page.locator(self.START_NEW_INSTEAD_BTN).first
        if start_new_btn.is_visible():
            logger.info("Draft panel found. Clicking 'Start New Instead'.")
            start_new_btn.click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1000)

    def resume_first_draft(self):
        """Resumes the first pending draft if visible."""
        resume_btn = self.page.locator(self.RESUME_DRAFT_TEXT).first
        if resume_btn.is_visible():
            logger.info("Draft panel found. Resuming first draft.")
            resume_btn.click()
            edit_btn = self.page.locator(self.EDIT_NEW_JOB_OPENING_BTN).first
            edit_btn.wait_for(state="visible", timeout=5000)
            edit_btn.click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1000)

    def close_drawer_safely(self, save_draft: bool = False):
        """Closes the drawer, handling the 'unsaved changes' dialog if it appears."""
        close_btn = self.page.get_by_role("button", name="Close").first
        if close_btn.is_visible():
            close_btn.click()
            self.page.wait_for_timeout(1000)

            unsaved_alert = self.page.locator("text=unsaved").first
            if unsaved_alert.is_visible():
                logger.info("Unsaved changes dialog detected.")
                if save_draft:
                    logger.info("Saving draft...")
                    self.page.get_by_role("button", name="Save as Draft").first.click()
                    try:
                        self.page.locator("text=Saved as draft").first.wait_for(state="visible", timeout=5000)
                    except Exception:
                        pass
                else:
                    logger.info("Discarding changes...")
                    discard_btn = self.page.get_by_role("button", name="Discard Changes").first
                    if discard_btn.is_visible():
                        discard_btn.click()
                    else:
                        self.page.keyboard.press("Escape")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(500)

    def clear_job_summary(self) -> tuple:
        """
        Clears the JD Summary SunEditor rich text area using real user keyboard actions.
        Focuses the editor, selects all content via Ctrl+A, and presses Backspace.
        
        Returns:
            tuple: (html_before, text_before, html_after, text_after)
        """
        editor = self.page.locator(self.JD_SUMMARY_EDITOR).first
        editor.wait_for(state="visible", timeout=10000)

        html_before = editor.evaluate("el => el.innerHTML")
        text_before = editor.inner_text()
        logger.debug(f"JD HTML before clear: {html_before}")
        logger.debug(f"JD text before clear: {text_before!r}")

        editor.scroll_into_view_if_needed()
        editor.click()
        self.page.keyboard.press("Control+a")
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(500)

        html_after = editor.evaluate("el => el.innerHTML")
        text_after = editor.inner_text()
        logger.debug(f"JD HTML after clear:  {html_after}")
        logger.debug(f"JD text after clear:  {text_after!r}")

        return html_before, text_before, html_after, text_after

    def get_latest_job_id(self) -> str:
        """Reads the newly created Job Posting ID from the grid."""
        job_id_locator = self.page.locator("text=/JOB_POSTING-\\d+/").first
        job_id_locator.wait_for(state="visible", timeout=5000)
        return job_id_locator.inner_text().strip()

    def get_first_draft_details(self) -> dict:
        """Retrieves details (title, draft_id, date) of the first draft on the list."""
        resume_btn = self.page.locator(self.RESUME_DRAFT_TEXT).first
        resume_btn.wait_for(state="visible", timeout=5000)

        card = resume_btn.locator("xpath=./ancestor::div[contains(., 'DRAFT-')][1]")
        card.wait_for(state="visible", timeout=5000)

        text = card.inner_text().strip()
        logger.info(f"First draft item scoped card text: '{text}'")

        clean_text = "".join(line.strip() for line in text.split("\n"))

        match = re.search(r"^(.+?)(DRAFT-\d+)\s*·\s*([\d-]+)\s*Resume\s*→$", clean_text)
        if match:
            return {
                "title": match.group(1).strip(),
                "draft_id": match.group(2).strip(),
                "date": match.group(3).strip(),
                "full_text": text
            }

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        title = lines[0] if lines else ""
        draft_id = ""
        m = re.search(r"(DRAFT-\d+)", lines[1] if len(lines) > 1 else "")
        if m:
            draft_id = m.group(1)

        return {"title": title, "draft_id": draft_id, "date": "", "full_text": text}

    def get_selected_option_text_by_label(self, label_hint: str) -> str:
        """Finds the select associated with label hint and returns selected option text."""
        selects = self.page.locator("select").all()
        for sel in selects:
            sel_id = sel.get_attribute("id") or ""
            if not sel_id:
                continue
            lbl_locator = self.page.locator(f"label[for='{sel_id}']").first
            if lbl_locator.count() > 0:
                lbl_text = lbl_locator.inner_text().strip()
                if label_hint.lower() in lbl_text.lower():
                    return self.page.evaluate("sel => sel.options[sel.selectedIndex].text", sel.element_handle()).strip()
        return ""
