from playwright.sync_api import Page, expect
import re
import random
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
    CREATE_JOB_BTN = "button:has-text('Create New Job Opening'), button:has-text('Create Job Opening'), a:has-text('Create New Job Opening')"
    BUSINESS_PROCESS = ".chakra-form-control:has(label:has-text('Business Process')) select, select:has(option:has-text('Business Process')), select[name*='business' i]"
    PAYROLL_COMPANY = ".chakra-form-control:has(label:has-text('Payroll Company')) select, select:has(option:has-text('Payroll Company')), select[name*='payroll' i]"
    BRANCH = ".chakra-form-control:has(label:has-text('Branch')) select, select:has(option:has-text('Branch')), select[name*='branch' i]"
    DEPARTMENT = ".chakra-form-control:has(label:has-text('Department')) select, select:has(option:has-text('Department')), select[name*='department' i]"
    JOB_TITLE = ".chakra-form-control:has(label:has-text('Job Title')) select, select:has(option:has-text('Job Title')), select[name*='job' i]"
    NUM_OPENINGS = "[placeholder='Enter Number of Openings'], input[placeholder*='Number of Openings' i]"
    EMPLOYMENT_TYPE = ".chakra-form-control:has(label:has-text('Employ')) select, select:has(option:has-text('Employ')), select[name*='employ' i]"
    OPENING_DATE = "[placeholder='Select Job Opening Date'], input[placeholder*='Opening Date' i]"
    CLOSING_DATE = "[placeholder='Select Job Closing Date'], input[placeholder*='Closing Date' i]"
    SALARY_MIN = "[placeholder='Enter Salary Min'], input[placeholder*='Salary Min' i]"
    SALARY_MAX = "[placeholder='Enter Salary Max'], input[placeholder*='Salary Max' i]"
    URGENCY_LEVEL = ".chakra-form-control:has(label:has-text('Urgency')) select, select:has(option:has-text('Urgency')), select[name*='urgency' i]"
    WORK_MODE = ".chakra-form-control:has(label:has-text('Work Mode')) select, select:has(option:has-text('Work Mode')), select[name*='work' i]"
    EXPECTED_JOIN_DATE = "[placeholder*='Select Expected Date of'], input[placeholder*='Expected Date' i]"
    EXP_MIN = "[placeholder='0 month'], [placeholder*='0 month' i]"
    EXP_MAX = "[placeholder='0 months'], [placeholder*='0 months' i]"
    PUBLISH_BTN = "button:has-text('Update Job'), button:has-text('Publish Job'), button:has-text('Publish')"
    CONFIRM_BTN = "button:has-text('Confirm')"
    ADDITIONAL_DETAILS = ".chakra-accordion__button:has-text('Additional Details'), button:has-text('Additional Details'), [role='button']:has-text('Additional Details'), :has-text('Additional Details')"

    # JD Summary - SunEditor contenteditable content area
    JD_SUMMARY_EDITOR = ".sun-editor-editable, .se-wrapper"

    # Draft Selectors
    DRAFT_MODAL_HEADER = ".chakra-modal__header:has-text('Pending Drafts Found'), .chakra-modal__header:has-text('Pending Draft Found'), header:has-text('Pending Drafts Found'), :has-text('Pending Drafts Found')"
    START_NEW_INSTEAD_BTN = "button.chakra-button:has-text('Start New Instead'), button:has-text('Start New Instead')"
    EDIT_NEW_JOB_OPENING_BTN = "button:has-text('Edit New Job Opening'), :has-text('Edit New Job Opening')"
    RESUME_DRAFT_TEXT = "p:has-text('Resume →'), p:has-text('Resume'), :has-text('Resume →')"

    # --- Atomic UI Interactions ---

    def navigate_to_active_jobs(self):
        """Navigates to Recruitment Portal -> Job Openings -> Active Jobs."""
        try:
            self.page.get_by_role("button", name="Recruitment Portal").click(timeout=5000)
            self.page.get_by_role("link", name="Job Openings").click(timeout=5000)
            self.page.get_by_role("link", name=re.compile(r"Active Jobs", re.I)).click(timeout=5000)
        except Exception:
            self.page.goto(f"{settings.BASE_URL}/active-jobs", timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")

    def click_create_new_job_opening(self):
        """Clicks the 'Create New Job Opening' button."""
        btn = self.page.locator(self.CREATE_JOB_BTN).first
        btn.wait_for(state="visible", timeout=8000)
        btn.click()

    def open_create_job_form(self):
        """
        Workflow: Active Jobs -> Create New Job -> Modal -> Click 'Start New Instead' -> Wait for Form
        """
        logger.info("[STEP] Click 'Create New Job Opening'")
        self.click_create_new_job_opening()

        start_new_btn = self.page.locator("button:has-text('Start New Instead')").first
        try:
            start_new_btn.wait_for(state="visible", timeout=4000)
            logger.info("[STEP] Draft Modal appeared → Clicking 'Start New Instead'")
            start_new_btn.click()
            try:
                start_new_btn.wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
        except Exception:
            logger.info("[INFO] No Draft Modal appeared, proceeding with form")

        logger.info("[STEP] Waiting for Job Creation Form...")
        self.page.locator(self.BUSINESS_PROCESS).first.wait_for(state="visible", timeout=10000)

    def is_draft_modal_visible(self, timeout: int = 4000) -> bool:
        """Returns True if the 'Pending Drafts Found' modal is visible."""
        modal_loc = self.page.locator(":has-text('Pending Drafts Found'), :has-text('Pending Draft Found'), p:has-text('Resume →'), button:has-text('Start New Instead'), :has-text('Start New Instead')").first
        try:
            modal_loc.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def start_new_instead(self):
        """Clicks the 'Start New Instead' button and waits for the creation form."""
        btn = self.page.locator("button:has-text('Start New Instead'), :has-text('Start New Instead')").first
        try:
            btn.wait_for(state="visible", timeout=8000)
            logger.info("Pending Drafts Found modal detected. Clicking 'Start New Instead'.")
            btn.click()
            try:
                btn.wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
            self.page.locator(self.BUSINESS_PROCESS).first.wait_for(state="visible", timeout=10000)
        except Exception as e:
            logger.debug(f"start_new_instead notice: {e}")

    def get_all_draft_items(self) -> list[dict]:
        """Collects all distinct draft cards currently listed in the modal by querying DRAFT- entries."""
        first_draft = self.page.locator("p:has-text('DRAFT-')").first
        try:
            first_draft.wait_for(state="visible", timeout=6000)
        except Exception:
            logger.debug("No draft cards appeared within timeout")
            return []

        draft_meta_locators = self.page.locator("p:has-text('DRAFT-')").all()
        drafts = []
        for idx, el in enumerate(draft_meta_locators):
            try:
                meta = el.inner_text().strip()
                card = el.locator("xpath=./ancestor::div[contains(., 'Resume')][1]")
                title = card.locator("p").first.inner_text().strip()

                draft_id = ""
                date = ""
                if "·" in meta:
                    parts = meta.split("·")
                    draft_id = parts[0].strip()
                    date = parts[1].strip()
                else:
                    m = re.search(r"(DRAFT-\d+)", meta)
                    if m:
                        draft_id = m.group(1)

                drafts.append({
                    "index": idx,
                    "title": title,
                    "draft_id": draft_id,
                    "date": date,
                    "meta": meta,
                    "locator": card
                })
            except Exception:
                pass
        draft_labels = [f"{d['title']} ({d['draft_id']})" for d in drafts]
        logger.info(f"Discovered {len(drafts)} distinct drafts in modal: {draft_labels}")
        return drafts

    def is_edit_job_opening_header_visible(self, timeout: int = 6000) -> bool:
        """Returns True if the 'Edit New Job Opening' header is visible."""
        header_loc = self.page.locator("header:has-text('Edit New Job Opening'), .chakra-modal__header:has-text('Edit New Job Opening'), :has-text('Edit New Job Opening')").first
        try:
            header_loc.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def resume_draft_by_index(self, index: int = 0) -> dict:
        """Picks a specific draft card by index, records its details, and clicks the draft directly."""
        drafts = self.get_all_draft_items()
        if not drafts:
            raise AssertionError("No drafts found in the 'Pending Drafts Found' modal")

        target = drafts[min(index, len(drafts) - 1)]
        logger.info(f"Picking Draft [{target['index']}]: Title='{target['title']}' | ID='{target['draft_id']}' | Date='{target['date']}'")

        target_card = target["locator"]
        target_card.click()

        # Handle optional intermediate 'Edit' button if drawer opens preview
        edit_btn = self.page.locator("button:has-text('Edit New Job Opening'), button:has-text('Edit Job Opening'), button:has-text('Edit')").first
        try:
            if edit_btn.is_visible(timeout=3000):
                logger.info("Clicking 'Edit' button to open editable draft form...")
                edit_btn.click()
        except Exception:
            pass

        self.page.wait_for_load_state("domcontentloaded")
        self.page.locator("header:has-text('Edit New Job Opening'), .chakra-form-control, select, button:has-text('Publish')").first.wait_for(state="visible", timeout=10000)
        return target

    def resume_random_draft(self) -> dict:
        """Picks a random draft card from the modal list, records its details, and clicks Resume."""
        drafts = self.get_all_draft_items()
        if not drafts:
            raise AssertionError("No drafts found in the 'Pending Drafts Found' modal")

        rand_idx = random.randint(0, len(drafts) - 1)
        return self.resume_draft_by_index(rand_idx)

    def resume_first_draft(self) -> dict:
        """Resumes the first pending draft."""
        return self.resume_draft_by_index(0)

    def close_drawer_safely(self, action: str = "discard", save_draft: bool = None):
        """
        Handles closing the job creation drawer and interacting with the 'You have unsaved changes' modal:
        - action='save' or save_draft=True: Clicks '<button>Save as Draft</button>'
        - action='discard' or save_draft=False: Clicks '<button>Discard Changes</button>'
        - action='keep_editing': Clicks '<button>Keep Editing</button>' (returns to existing form)
        """
        if save_draft is not None:
            action = "save" if save_draft else "discard"

        close_btn = self.page.locator("button.chakra-modal__close-btn, button[aria-label*='Close' i], button:has-text('Close')").first
        try:
            if close_btn.is_visible(timeout=2000):
                close_btn.click()
            else:
                self.page.keyboard.press("Escape")
        except Exception:
            self.page.keyboard.press("Escape")

        unsaved_modal = self.page.locator("p:has-text('You have unsaved changes'), :has-text('You have unsaved changes')").first
        try:
            if unsaved_modal.is_visible(timeout=3000):
                logger.info(f"Unsaved changes modal detected: 'You have unsaved changes'. Action='{action}'")
                if action == "save":
                    save_btn = self.page.locator("button:has-text('Save as Draft')").first
                    save_btn.wait_for(state="visible", timeout=3000)
                    save_btn.click()
                    try:
                        self.page.locator("text=Saved as draft").first.wait_for(state="visible", timeout=5000)
                    except Exception:
                        pass
                elif action == "discard":
                    discard_btn = self.page.locator("button:has-text('Discard Changes')").first
                    discard_btn.wait_for(state="visible", timeout=3000)
                    discard_btn.click()
                elif action == "keep_editing":
                    keep_btn = self.page.locator("button:has-text('Keep Editing')").first
                    keep_btn.wait_for(state="visible", timeout=3000)
                    keep_btn.click()
        except Exception:
            pass
        self.page.wait_for_load_state("domcontentloaded")

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
        """Retrieves details (title, draft_id, date) of the first draft card in the modal."""
        drafts = self.get_all_draft_items()
        if not drafts:
            raise AssertionError("No drafts found in the 'Pending Drafts Found' modal")
        return drafts[0]

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
                    try:
                        return self.page.evaluate("sel => sel.options[sel.selectedIndex].text", sel.element_handle()).strip()
                    except Exception:
                        pass
        return ""

    def expand_additional_details(self):
        """Scrolls to and expands the Additional Details accordion section."""
        btn = self.page.locator(self.ADDITIONAL_DETAILS).first
        btn.wait_for(state="visible", timeout=8000)
        btn.scroll_into_view_if_needed()
        btn.click()
        try:
            self.page.locator(self.EXP_MIN).first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

    def select_business_process(self, index: int = 1) -> str:
        loc = self.page.locator(self.BUSINESS_PROCESS).first
        loc.wait_for(state="visible", timeout=8000)
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Business Process")

    def select_payroll_company(self, index: int = 1) -> str:
        loc = self.page.locator(self.PAYROLL_COMPANY).first
        loc.wait_for(state="visible", timeout=8000)
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Payroll Company")

    def select_branch(self, index: int = 1) -> str:
        loc = self.page.locator(self.BRANCH).first
        loc.wait_for(state="visible", timeout=8000)
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Branch")

    def select_department(self, index: int = 1) -> str:
        loc = self.page.locator(self.DEPARTMENT).first
        loc.wait_for(state="visible", timeout=8000)
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Department")

    def select_job_title(self, index: int = 1) -> str:
        loc = self.page.locator(self.JOB_TITLE).first
        loc.wait_for(state="visible", timeout=8000)
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Job Title")

    def select_random_job_title(self, exclude_title: str = None) -> str:
        """Dynamically selects a random valid Job Title from the dropdown, optionally excluding a specific title."""
        loc = self.page.locator(self.JOB_TITLE).first
        loc.wait_for(state="visible", timeout=8000)
        options = loc.locator("option").all()
        valid = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val and text and "select" not in text.lower():
                if exclude_title and text.lower() == exclude_title.lower():
                    continue
                valid.append(val)
        if valid:
            chosen_val = random.choice(valid)
            loc.select_option(value=chosen_val)
            return self.get_selected_option_text_by_label("Job Title")
        return ""

    def select_employment_type(self, index: int = 1) -> str:
        loc = self.page.locator(self.EMPLOYMENT_TYPE).first
        loc.wait_for(state="visible", timeout=8000)
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Employ")

    def select_urgency_level(self, index: int = 1) -> str:
        loc = self.page.locator(self.URGENCY_LEVEL).first
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Urgency")

    def select_work_mode(self, index: int = 1) -> str:
        loc = self.page.locator(self.WORK_MODE).first
        loc.select_option(index=index)
        return self.get_selected_option_text_by_label("Work Mode")

    def fill_job_fields(self, num_openings: str = "1", opening_date: str = None, closing_date: str = None,
                        salary_min: str = "15000", salary_max: str = "25000", doj: str = None,
                        min_exp: str = "1", max_exp: str = "3"):
        """Fills standard numeric, date, and experience fields."""
        if num_openings:
            self.page.locator(self.NUM_OPENINGS).first.fill(num_openings)
        if opening_date:
            self.page.locator(self.OPENING_DATE).first.fill(opening_date)
        if closing_date:
            self.page.locator(self.CLOSING_DATE).first.fill(closing_date)
        if salary_min:
            self.page.locator(self.SALARY_MIN).first.fill(salary_min)
        if salary_max:
            self.page.locator(self.SALARY_MAX).first.fill(salary_max)
        if doj:
            self.page.locator(self.EXPECTED_JOIN_DATE).first.fill(doj)

        if min_exp or max_exp:
            self.expand_additional_details()
            if min_exp:
                self.page.locator(self.EXP_MIN).first.fill(min_exp)
            if max_exp:
                self.page.locator(self.EXP_MAX).first.fill(max_exp)

    def set_job_summary(self, text: str):
        """Fills text into the JD Summary editor."""
        editor = self.page.locator(self.JD_SUMMARY_EDITOR).first
        editor.wait_for(state="visible", timeout=8000)
        editor.scroll_into_view_if_needed()
        editor.click()
        self.page.keyboard.press("Control+a")
        self.page.keyboard.press("Backspace")
        self.page.keyboard.type(text, delay=10)

    def click_generate_ai_jd(self) -> str:
        """Clicks 'Generate JD with AI', waits for completion, and returns generated summary text."""
        btn = self.page.get_by_role("button", name=re.compile(r"Generate JD with AI|Generate.*AI", re.I)).first
        btn.wait_for(state="visible", timeout=8000)
        btn.scroll_into_view_if_needed()
        btn.click()
        
        # Wait for spinner to disappear
        try:
            self.page.locator(".chakra-button__spinner, .chakra-spinner").first.wait_for(state="hidden", timeout=35000)
        except Exception:
            pass

        editor = self.page.locator(self.JD_SUMMARY_EDITOR).first
        editor.wait_for(state="visible", timeout=10000)
        text = ""
        for _ in range(30):
            text = editor.inner_text().strip()
            if len(text) > 10:
                break
            self.page.wait_for_timeout(1000)

        logger.info(f"AI JD Generated text length: {len(text)}")
        return text

    def verify_validation_message_visible(self, message: str):
        """Verifies that a validation message is visible on the page."""
        loc = self.page.get_by_text(message, exact=False).first
        expect(loc).to_be_visible(timeout=5000)

    def get_all_error_messages(self) -> list[str]:
        """Collects all visible field-level error messages."""
        try:
            self.page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error']").first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

        errors = []
        locs = self.page.locator(".chakra-form__error-message, [id*='feedback'], [id*='error']").all()
        for loc in locs:
            try:
                if loc.is_visible():
                    txt = loc.inner_text().strip()
                    if txt and txt not in errors:
                        errors.append(txt)
            except Exception:
                pass
        logger.info(f"Discovered field validation errors: {errors}")
        return errors
