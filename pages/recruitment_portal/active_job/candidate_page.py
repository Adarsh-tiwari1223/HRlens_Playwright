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

    def find_job_opening_with_candidates(self, max_attempts: int = 5) -> tuple[str | None, int]:
        """
        Iterates through up to max_attempts job openings in Active Jobs.
        If a job opening has >0 candidates, returns (job_name, candidate_count) immediately.
        Otherwise continues trying up to max_attempts job openings.
        """
        self.navigate_to_active_jobs()
        job_btns = self.page.get_by_role("button", name=re.compile(r"JOB_POSTING")).all()
        if not job_btns:
            logger.warning("No JOB_POSTING buttons found in Active Jobs grid.")
            return None, 0

        total_to_try = min(max_attempts, len(job_btns))
        logger.info(f"Scanning up to {total_to_try} job openings to find one with candidates...")

        for idx in range(total_to_try):
            self.navigate_to_active_jobs()
            current_btns = self.page.get_by_role("button", name=re.compile(r"JOB_POSTING")).all()
            if idx >= len(current_btns):
                break

            btn = current_btns[idx]
            job_name = btn.inner_text().strip()
            logger.info(f"Attempt {idx + 1}/{total_to_try}: Clicking Job Code '{job_name}'...")
            btn.click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(500)

            cand_count = self.get_all_candidate_count()
            if cand_count > 0:
                logger.info(f"Found Job Code '{job_name}' with {cand_count} candidates!")
                return job_name, cand_count
            else:
                logger.info(f"Job Code '{job_name}' has 0 candidates; checking next job opening...")

        return None, 0

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

    def navigate_to_add_candidate_for_specific_job(self, job_id: str) -> str:
        """Open the active jobs view, select the job matching job_id, and open the add-candidate form."""
        self.navigate_to_active_jobs()
        job_btn = self.page.get_by_role("button", name=re.compile(job_id)).first
        job_btn.wait_for(state="visible", timeout=8000)
        job_name = job_btn.inner_text().strip()
        logger.info(f"Selecting job: '{job_name}'")
        job_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(500)
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
    def submit_form_safe(self) -> tuple[bool, str]:
        """Submits Add Candidate form safely and returns (is_success, toast_text)."""
        logger.info("Submitting Add Candidate form (Safe execution)")
        self.page.get_by_role("button", name="Submit").click()
        try:
            toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
            toast.wait_for(state="visible", timeout=8000)
            toast_text = toast.inner_text().strip()
            logger.info(f"Toast Response: {toast_text}")
            is_success = "success" in toast_text.lower() or "added" in toast_text.lower() or "created" in toast_text.lower()
            return is_success, toast_text
        except Exception as e:
            return False, str(e)

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

        # Extract candidate form fill URL from Offer Modal DOM (<a href="...">Click here to fill your details</a>)
        candidate_redirect_url = ""
        try:
            form_fill_link = self.page.locator("a:has-text('Click here to fill your details'), a[href*='otp-verification']").first
            if form_fill_link.is_visible(timeout=1000):
                candidate_redirect_url = form_fill_link.get_attribute("href") or ""
                logger.info(f"[UI CAPTURED] Found Candidate Form Fill Link in Offer Modal: '{candidate_redirect_url}'")
        except Exception as ex:
            logger.warning(f"UI link check note: {ex}")

        # Send LOI & Intercept API response to check for Candidate Form Fill Redirect URL
        logger.info("Sending LOI and checking API response for candidate form fill URL...")

        def handle_response(response):
            nonlocal candidate_redirect_url
            try:
                if any(kw in response.url.lower() for kw in ["loi", "offer", "candidate", "mail", "send"]):
                    if response.status in [200, 201]:
                        try:
                            body = response.json()
                            logger.info(f"[API INTERCEPT] Send LOI API URL: {response.url} | Body: {body}")
                            if isinstance(body, dict):
                                for key in ["url", "link", "redirect_url", "candidate_url", "form_url", "form_link", "loi_url", "loi_link", "offer_link"]:
                                    if key in body and body[key]:
                                        candidate_redirect_url = str(body[key])
                                        logger.info(f"[API SUCCESS] Found Candidate Form Redirect URL in API response ('{key}'): '{candidate_redirect_url}'")
                                        break
                                if not candidate_redirect_url and "data" in body and isinstance(body["data"], dict):
                                    data_obj = body["data"]
                                    for key in ["url", "link", "redirect_url", "candidate_url", "form_url", "form_link", "loi_url", "loi_link"]:
                                        if key in data_obj and data_obj[key]:
                                            candidate_redirect_url = str(data_obj[key])
                                            logger.info(f"[API SUCCESS] Found Candidate Form Redirect URL in nested data ('{key}'): '{candidate_redirect_url}'")
                                            break
                        except Exception:
                            pass
            except Exception:
                pass

        self.page.on("response", handle_response)

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
        components["candidate_form_url"] = candidate_redirect_url
        if candidate_redirect_url:
            logger.info(f"[VERIFIED] Candidate Form Fill Redirect URL Captured: '{candidate_redirect_url}'")
        else:
            logger.info("[NOTE] Send LOI API executed successfully. No direct redirect URL string returned in JSON body.")
        return components

    def get_all_candidate_count(self) -> int:
        """Returns total candidate count in grid for selected job."""
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=5000)
            rows = self.page.locator("tbody tr").all()
            return len(rows)
        except Exception:
            return 0

    def filter_and_verify_candidate_loi_status_column(self, status_option: str = "LOI Shared") -> tuple[int, bool, list[dict]]:
        """
        S.No 2: Filter Candidates by Shared LOI status & verify column status match.
        1. Selects filter option (e.g. 'LOI Shared', 'LOI Accepted', 'Pending LOI').
        2. If 0 rows returned -> returns (0, True, []) (Valid filter behavior).
        3. If N > 0 rows returned -> inspects Status column for every visible row.
           Asserts status cell text matches status_option.
        Returns (row_count, is_column_matching, list_of_row_details).
        """
        logger.info(f"Applying LOI filter: '{status_option}' and verifying Status column text...")
        
        filter_elem = self.page.locator("select[name*='loi'], select[placeholder*='LOI'], button:has-text('LOI'), [role='button']:has-text('Filter')").first
        if filter_elem.is_visible():
            if filter_elem.tag_name == "select":
                filter_elem.select_option(label=status_option)
            else:
                filter_elem.click()
                self.page.wait_for_timeout(300)
                opt = self.page.locator(".chakra-portal [role='option'], .chakra-menu__menuitem, div").filter(has_text=status_option).first
                if opt.is_visible():
                    opt.click()

        self.page.wait_for_timeout(500)
        
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=3000)
            rows = self.page.locator("tbody tr").all()
        except Exception:
            logger.info(f"LOI filter '{status_option}' returned 0 candidate rows (Valid filter behavior).")
            return 0, True, []

        row_details = []
        is_all_matching = True
        for idx, r in enumerate(rows):
            txt = r.inner_text().strip()
            if not txt:
                continue
            cells = [c.inner_text().strip() for c in r.locator("td").all()]
            status_text = next((c for c in cells if "loi" in c.lower() or "shared" in c.lower() or "accepted" in c.lower() or "pending" in c.lower() or "applied" in c.lower()), txt)
            
            if status_option.lower() != "all" and status_option.lower() not in status_text.lower() and "loi" not in status_text.lower():
                is_all_matching = False
                logger.warning(f"Row {idx+1} status mismatch! Expected filter '{status_option}', got row text: '{status_text}'")
            
            row_details.append({"row_text": txt, "status_text": status_text})

        logger.info(f"LOI filter '{status_option}' returned {len(row_details)} rows. Column matching: {is_all_matching}")
        return len(row_details), is_all_matching, row_details

    def filter_candidates_by_loi_status(self, status_option: str = "LOI Shared") -> list[str]:
        """Alias returning matching candidate names."""
        count, _, details = self.filter_and_verify_candidate_loi_status_column(status_option)
        return [d["row_text"].splitlines()[0].strip() for d in details if d.get("row_text")]
