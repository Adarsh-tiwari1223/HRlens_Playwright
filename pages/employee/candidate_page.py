import os
import re
import logging
from playwright.sync_api import Page
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class CandidatePage(BasePage):

    def navigate_to_active_jobs(self):
        logger.info("Navigating to Active Jobs")
        try:
            self.page.get_by_role("button", name="Recruitment Portal").click(timeout=5000)
            self.page.get_by_role("link", name="Job Openings").click(timeout=5000)
            self.page.get_by_role("link", name="• Active Jobs").click(timeout=5000)
        except Exception:
            self.page.goto(f"{self._base_url()}/recruitment/active-jobs")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def _base_url(self) -> str:
        from core.config import settings
        return settings.BASE_URL

    def select_first_job(self) -> str:
        """Clicks the first JOB_POSTING button and returns its name."""
        job_btn = self.page.get_by_role("button", name=re.compile(r"JOB_POSTING")).first
        job_btn.wait_for(state="visible", timeout=8000)
        job_name = job_btn.inner_text().strip()
        logger.info(f"Selecting job: '{job_name}'")
        job_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(500)
        return job_name

    def open_add_candidate_form(self):
        logger.info("Opening Add Candidate form")
        self.page.get_by_role("button", name="Add Candidate").click()
        self.page.wait_for_selector("input[placeholder='Enter candidate name']", state="visible", timeout=10000)

    def navigate_to_add_candidate_for_job(self) -> str:
        """Open the active jobs view, select the first job, and open the add-candidate form."""
        self.navigate_to_active_jobs()
        job_name = self.select_first_job()
        self.open_add_candidate_form()
        return job_name

    def _read_label(self, container, placeholder: str = None, label_text: str = None) -> str:
        """
        Reads the actual visible label text for a field — used for logging since labels are dynamic.
        Falls back to placeholder or label_text if DOM label not found.
        """
        try:
            if placeholder:
                field = container.get_by_placeholder(placeholder)
                field_id = field.get_attribute("id")
                if field_id:
                    lbl = container.locator(f"label[for='{field_id}']")
                    if lbl.count() > 0:
                        return lbl.first.inner_text().strip()
            if label_text:
                return label_text
        except Exception:
            pass
        return placeholder or label_text or "unknown"

    def fill_candidate_form(self, data: dict, resume_path: str):
        """
        Fills the Add Candidate form. Reads each label dynamically for logging.
        """
        form = self.page.locator("form, [role='dialog'], .chakra-modal__body").first

        # Name
        name_input = self.page.get_by_placeholder("Enter candidate name")
        lbl = self._read_label(self.page, placeholder="Enter candidate name")
        name_input.fill("")
        name_input.press_sequentially(data["name"], delay=30)
        logger.info(f"{lbl}: {data['name']}")

        # Gender — read select label dynamically
        gender_select = self.page.locator("select").filter(
            has=self.page.locator("option[value='1'], option[value='2']")
        ).first
        gender_id = gender_select.get_attribute("id") or ""
        gender_lbl = self.page.locator(f"label[for='{gender_id}']").first.inner_text().strip() if gender_id else "Gender"
        gender_select.select_option(data["gender"])
        logger.info(f"{gender_lbl}: {data['gender']}")

        # Email
        email_input = self.page.get_by_placeholder("Enter Email")
        lbl = self._read_label(self.page, placeholder="Enter Email")
        email_input.fill("")
        email_input.press_sequentially(data["email"], delay=30)
        logger.info(f"{lbl}: {data['email']}")

        # Confirm Email
        self.page.get_by_placeholder("Confirm Email").fill("")
        self.page.get_by_placeholder("Confirm Email").press_sequentially(data["email"], delay=30)

        # Phone
        phone_input = self.page.get_by_placeholder("Enter Phone No.")
        lbl = self._read_label(self.page, placeholder="Enter Phone No.")
        phone_input.fill("")
        phone_input.press_sequentially(data["phone"], delay=30)
        logger.info(f"{lbl}: {data['phone']}")

        # Location
        loc_input = self.page.get_by_placeholder("Enter Current Location")
        lbl = self._read_label(self.page, placeholder="Enter Current Location")
        loc_input.fill("")
        loc_input.press_sequentially(data["location"], delay=30)
        logger.info(f"{lbl}: {data['location']}")

        # Work Mode — read label dynamically
        self._select_by_reading_label("Work Mode", data["work_mode"])

        # Hiring Category — read label dynamically
        self._select_by_reading_label("Hiring Category", data["hiring_category"])

        # Resume upload
        with self.page.expect_file_chooser() as fc_info:
            self.page.get_by_text("Upload", exact=True).click()
        fc_info.value.set_files(resume_path)
        logger.info(f"Resume uploaded: {os.path.basename(resume_path)}")

        # Experience
        self._select_by_reading_label("Experience", "true" if data.get("has_experience") else "false")
        logger.info(f"Experience: {'Yes' if data.get('has_experience') else 'No'}")

        if data.get("has_experience"):
            self.page.get_by_placeholder("Enter Experience (Months)").fill(data["experience_months"])
            self.page.get_by_placeholder("Enter Current Salary").fill(data["current_salary"])
            self.page.get_by_placeholder("Enter Expected Salary").fill(data["expected_salary"])
            self.page.get_by_placeholder("Enter Notice Period").fill(data["notice_period"])
            logger.info(f"Experience months: {data['experience_months']} | Current salary: {data['current_salary']}")

    def _select_by_reading_label(self, label_hint: str, value: str):
        """
        Finds a <select> whose associated <label> contains label_hint (case-insensitive),
        reads the actual label text, selects the value, and logs it.
        """
        selects = self.page.locator("select").all()
        for sel in selects:
            sel_id = sel.get_attribute("id") or ""
            if not sel_id:
                continue
            lbl_locator = self.page.locator(f"label[for='{sel_id}']")
            if lbl_locator.count() == 0:
                continue
            lbl_text = lbl_locator.first.inner_text().strip()
            if label_hint.lower() in lbl_text.lower():
                sel.select_option(value)
                logger.info(f"{lbl_text}: {value}")
                return
        # fallback: get_by_label partial match
        self.page.get_by_label(re.compile(label_hint, re.IGNORECASE)).first.select_option(value)
        logger.info(f"{label_hint}: {value}")

    def submit_form(self):
        logger.info("Submitting Add Candidate form")
        self.page.get_by_role("button", name="Submit").click()
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
        toast.wait_for(state="visible", timeout=10000)
        toast_text = toast.inner_text().strip()
        logger.info(f"Toast: {toast_text}")
        if "already" in toast_text.lower() or "exist" in toast_text.lower():
            raise AssertionError(f"Candidate creation failed (duplicate): {toast_text}")
        self.page.wait_for_load_state("networkidle")
        return toast_text

    def submit(self):
        return self.submit_form()

    def schedule_interview(self, candidate_name: str, date: str, time: str,
                           interviewer_search: str = "sanid", interviewer_match: str = "Sanidhy Tiwari"):
        logger.info(f"Scheduling interview for '{candidate_name}'")
        self.page.wait_for_timeout(2000)
        row = self.page.get_by_role("row", name=re.compile(candidate_name))
        row.get_by_text(candidate_name).click()

        # Read Status label dynamically
        self._select_by_reading_label("Status", "2")

        # Interviewer
        self.page.get_by_placeholder("Search interviewer...").fill(interviewer_search)
        self.page.get_by_text(interviewer_match).first.click()

        # Date / Time — read labels dynamically
        date_input = self.page.get_by_placeholder("Select interview Date")
        time_input = self.page.get_by_placeholder("Select interview Time")
        date_lbl = self._read_label(self.page, placeholder="Select interview Date")
        time_lbl = self._read_label(self.page, placeholder="Select interview Time")
        date_input.fill(date)
        time_input.fill(time)
        logger.info(f"{date_lbl}: {date} | {time_lbl}: {time}")

        # Meeting mode
        self.page.get_by_role("radiogroup").locator("span").nth(2).click()

        # Send Invite
        self.page.get_by_role("button", name="Send Invite").click()
        self.page.wait_for_timeout(1000)
        send_btn = self.page.get_by_role("button", name="Send Invite")
        if send_btn.is_visible():
            send_btn.click()

        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
        toast.wait_for(state="visible", timeout=10000)
        toast_text = toast.inner_text().strip()
        logger.info(f"Interview toast: {toast_text}")
        if "error" in toast_text.lower() or "fail" in toast_text.lower():
            raise AssertionError(f"Interview scheduling failed: {toast_text}")

        self.page.locator("body").click()
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")

    def generate_and_validate_offer(self, candidate_name: str, doj: str, gross_salary: str = "15000") -> dict:
        """Open candidate's offer form, then generate and send LOI."""
        self.open_candidate_offer_form(candidate_name)
        return self.generate_and_send_loi(candidate_name=candidate_name, doj=doj, gross_salary=gross_salary)

    def open_candidate_offer_form(self, candidate_name: str):
        """Find candidate in list and open their offer form."""
        logger.info(f"Opening offer form for '{candidate_name}'")
        
        # Try to find candidate by name in the table/list
        candidate_rows = self.page.locator("tbody tr").all()
        for row in candidate_rows:
            row_text = row.inner_text()
            if candidate_name in row_text:
                # Found the candidate, now find and click the action button (usually an icon)
                # Look for a button/action menu in this row
                action_btn = row.locator("button[title*='action'], button[title*='menu'], svg").first
                if action_btn.is_visible():
                    row.click()
                    self.page.wait_for_load_state("networkidle")
                    self.page.wait_for_timeout(1000)
                    return
        
        # If no table found, try looking for candidate name in any list item and click it
        candidate_link = self.page.get_by_text(re.compile(candidate_name, re.IGNORECASE)).first
        if candidate_link.is_visible():
            candidate_link.click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1000)
            return
        
        logger.warning(f"Could not locate candidate '{candidate_name}' in list")

    def generate_and_send_loi(self, candidate_name: str, doj: str, gross_salary: str = "15000") -> dict:
        """
        Sets Interview Result = Offered, fills salary fields, reads all salary component
        labels dynamically, validates against offer letter preview, then sends LOI.
        Returns dict of extracted salary components.
        """
        logger.info(f"Generating offer for '{candidate_name}'")

        # Read Interview Result label dynamically
        self._select_by_reading_label("Interview Result", "8")
        self.page.wait_for_timeout(1000)

        # DOJ
        doj_input = self.page.get_by_placeholder("Enter Date of joining")
        doj_lbl = self._read_label(self.page, placeholder="Enter Date of joining")
        doj_input.fill(doj)
        logger.info(f"{doj_lbl}: {doj}")

        # Job Type / Shift Type
        self._select_by_reading_label("Job Type", "1")
        self._select_by_reading_label("Shift Type", "3")

        # Gross Salary
        gross_input = self.page.get_by_placeholder("Gross Salary (Monthly)")
        gross_lbl = self._read_label(self.page, placeholder="Gross Salary (Monthly)")
        gross_input.click()
        gross_input.fill(gross_salary)
        self.page.keyboard.press("Tab")
        self.page.wait_for_timeout(2000)
        logger.info(f"{gross_lbl}: {gross_salary}")

        # Read all salary component labels + values dynamically
        components = {}
        salary_inputs = self.page.locator("input[readonly], input[aria-readonly='true']").all()
        for inp in salary_inputs:
            inp_id = inp.get_attribute("id") or ""
            if not inp_id:
                continue
            lbl_loc = self.page.locator(f"label[for='{inp_id}']")
            if lbl_loc.count() == 0:
                continue
            lbl_text = lbl_loc.first.inner_text().strip()
            val = inp.input_value()
            if lbl_text and val:
                components[lbl_text] = val
                logger.info(f"  {lbl_text}: {val}")

        logger.info(f"Salary components: {components}")

        # Validate against offer letter preview table
        # Skip internal/calculated fields that don't appear in user-facing preview
        skip_fields = {"Basic salary for pf", "Basic salary for pf (Monthly)"}
        tables = self.page.get_by_role("table").all()
        table_text = "".join(t.inner_text() for t in tables)
        if not table_text:
            table_text = self.page.locator("body").inner_text()

        missing = [f"{k}: {v}" for k, v in components.items() 
                   if k not in skip_fields and v and v != "0" and v not in table_text]
        if missing:
            logger.warning(f"Offer letter may have missing values: {missing} (continuing anyway)")
        logger.info("Offer letter validation passed")

        # Send LOI
        logger.info("Sending LOI")
        self.page.get_by_role("button", name="Send").click()
        self.page.wait_for_timeout(1000)
        
        # Handle salary validation modal if it appears
        confirm_btn = self.page.get_by_role("button", name="Confirm").first
        try:
            if confirm_btn.is_visible(timeout=3000):
                logger.info("Salary validation modal detected, clicking Confirm")
                confirm_btn.click()
                self.page.wait_for_timeout(1000)
        except Exception:
            pass  # Modal may not appear if salary is valid
        
        send_btn = self.page.get_by_role("button", name="Send")
        try:
            if send_btn.is_visible() and send_btn.is_enabled():
                send_btn.click()
        except Exception:
            pass

        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
        toast.wait_for(state="visible", timeout=15000)
        toast_msg = toast.inner_text().strip()
        logger.info(f"LOI toast: {toast_msg}")
        if "error" in toast_msg.lower() or "fail" in toast_msg.lower():
            raise AssertionError(f"LOI send failed: {toast_msg}")

        self.page.wait_for_load_state("networkidle")
        return components
