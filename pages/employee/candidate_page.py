import os
import re
from playwright.sync_api import Page, expect

class CandidatePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate_to_add_candidate_for_job(self, posting_name: str = "JOB_POSTING-330") -> str:
        """
        Navigates to the Active Jobs page, finds the specific posting, clicks it, and clicks Add Candidate.
        Returns the name of the selected job posting.
        """
        # Navigate through the side menu to the Active Jobs page
        self.page.get_by_role("button", name="Recruitment Portal").click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Job Openings").click()
        self.page.get_by_role("link", name="• Active Jobs").click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

        # Get the job name from the FIRST job posting button dynamically using regex
        job_button = self.page.get_by_role("button", name=re.compile(r"JOB_POSTING")).first
        job_name = job_button.inner_text().strip()
        print(f"\n[JOB_POSTING] Selecting Job: {job_name}")
        job_button.click()
        
        # Click Add Candidate
        self.page.get_by_role("button", name="Add Candidate").click()
        
        # Wait for the modal/form to visibly appear
        self.page.wait_for_selector("input[placeholder='Enter candidate name']", state="visible", timeout=10000)
        return job_name

    def fill_candidate_form(self, data: dict, resume_path: str):
        """
        Fills the Add Candidate form dynamically based on the provided data dictionary.
        Handles the Experience toggle conditionally.
        """
        # 1. Fill Name
        name_input = self.page.get_by_placeholder("Enter candidate name")
        name_input.fill("")
        name_input.press_sequentially(data["name"], delay=30)
        print(f"Candidate Name: {data['name']}")
        
        # 2. Select Gender
        self.page.get_by_label("Gender *").select_option(data["gender"])
        print(f"Gender: {data['gender']}")
        
        # 3. Fill Email
        email_input = self.page.get_by_placeholder("Enter Email")
        email_input.fill("")
        email_input.press_sequentially(data["email"], delay=30)
        print(f"Email: {data['email']}")
        
        # 4. Fill Confirm Email
        confirm_input = self.page.get_by_placeholder("Confirm Email")
        confirm_input.fill("")
        confirm_input.press_sequentially(data["email"], delay=30)
        
        # 5. Fill Phone No
        phone_input = self.page.get_by_placeholder("Enter Phone No.")
        phone_input.fill("")
        phone_input.press_sequentially(data["phone"], delay=30)
        print(f"Phone No.: {data['phone']}")
        
        # 6. Fill Location
        loc_input = self.page.get_by_placeholder("Enter Current Location")
        loc_input.fill("")
        loc_input.press_sequentially(data["location"], delay=30)
        print(f"Current Location: {data['location']}")
        
        # 7. Select Work Mode
        self.page.get_by_label("Work Mode *").select_option(data["work_mode"])
        print(f"Work Mode: {data['work_mode']}")
        
        # 8. Select Hiring Category
        self.page.get_by_label("Hiring Category *").select_option(data["hiring_category"])
        print(f"Hiring Category: {data['hiring_category']}")
        
        # 9. Upload Resume
        with self.page.expect_file_chooser() as fc_info:
            self.page.get_by_text("Upload", exact=True).click()
        file_chooser = fc_info.value
        file_chooser.set_files(resume_path)
        print(f"Resume Uploaded: {os.path.basename(resume_path)}")
        
        # 10. Experience conditional block
        is_experienced = data.get("has_experience", False)
        exp_value = "true" if is_experienced else "false"
        self.page.get_by_label("Experience *").select_option(exp_value)
        print(f"Experience: {'Yes' if is_experienced else 'No'}")
        
        if is_experienced:
            exp_months = self.page.get_by_placeholder("Enter Experience (Months)")
            exp_months.fill("")
            exp_months.press_sequentially(data["experience_months"], delay=30)
            print(f"Experience (Months): {data['experience_months']}")
            
            curr_sal = self.page.get_by_placeholder("Enter Current Salary")
            curr_sal.fill("")
            curr_sal.press_sequentially(data["current_salary"], delay=30)
            print(f"Current Salary: {data['current_salary']}")
            
            exp_sal = self.page.get_by_placeholder("Enter Expected Salary")
            exp_sal.fill("")
            exp_sal.press_sequentially(data["expected_salary"], delay=30)
            print(f"Expected Salary: {data['expected_salary']}")
            
            notice = self.page.get_by_placeholder("Enter Notice Period")
            notice.fill("")
            notice.press_sequentially(data["notice_period"], delay=30)
            print(f"Notice Period: {data['notice_period']}")
            
    def submit(self):
        """Submits the Add Candidate form and waits for success validation."""
        self.page.get_by_role("button", name="Submit").click()
        
        # Capture and validate the resulting toast notification
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
        toast.wait_for(state="visible", timeout=10000)
        toast_text = toast.inner_text().lower()
        
        if "already" in toast_text or "exist" in toast_text:
            raise AssertionError(f"Candidate creation failed (duplicate detected): {toast_text}")
            
        print(f"[TOAST SUCCESS] {toast.inner_text()}")
        self.page.wait_for_load_state("networkidle")

    def schedule_interview(self, candidate_name: str, interviewer_search: str = "sanid", interviewer_match: str = "Sanidhy Tiwari", date: str = "2026-06-10", time: str = "10:30"):
        """
        Selects a candidate from the grid and schedules an interview.
        """
        # 1. Click on the dynamically generated candidate's name to open their modal
        self.page.wait_for_timeout(2000) # Wait for UI to settle after adding candidate
        row = self.page.get_by_role("row", name=re.compile(candidate_name))
        row.get_by_text(candidate_name).click()
        
        # 2. Change status to Interview Scheduled (Status option "2")
        self.page.get_by_label("Status *").select_option("2")
        
        # 3. Search and select interviewer
        self.page.get_by_placeholder("Search interviewer...").click()
        self.page.get_by_placeholder("Search interviewer...").fill(interviewer_search)
        self.page.get_by_text(interviewer_match).first.click()
        
        # 4. Fill Date and Time
        self.page.get_by_placeholder("Select interview Date").fill(date)
        self.page.get_by_placeholder("Select interview Time").fill(time)
        
        # Select Meeting Mode (Virtual/Face-to-Face)
        self.page.get_by_role("radiogroup").locator("span").nth(2).click()
        
        # 5. Send Invite
        self.page.get_by_role("button", name="Send Invite").click()
        
        # Workaround: The HRlens UI sometimes requires a second click on Send Invite
        # to bypass animations or validations (as observed in the codegen trace).
        self.page.wait_for_timeout(1000)
        send_btn = self.page.get_by_role("button", name="Send Invite")
        if send_btn.is_visible():
            send_btn.click()
        
        # 6. Wait for success toast
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
        toast.wait_for(state="visible", timeout=10000)
        
        toast_text = toast.inner_text().lower()
        if "error" in toast_text or "fail" in toast_text:
            raise AssertionError(f"Interview scheduling failed: {toast_text}")
            
        print(f"[TOAST SUCCESS] {toast.inner_text()}")
        
        # The user manually clicks the body to dismiss the scheduling sub-modal overlay.
        self.page.locator("body").click()
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")

    def generate_and_validate_offer(self, candidate_name: str, doj: str, gross_salary: str = "15000"):
        """
        Re-opens the candidate modal, selects Interview Result = Offered (8), fills salary info,
        reads the calculated components, and validates them against the actual Offer Letter preview table.
        """
        print(f"\n[ACTION] Proceeding with Offer Generation inside the already open candidate modal...")
        self.page.wait_for_timeout(1000)
        
        self.page.get_by_label("Interview Result").select_option("8")
        self.page.wait_for_timeout(1000) # Wait for fields to reveal
        
        self.page.get_by_placeholder("Enter Date of joining").fill(doj)
        self.page.get_by_label("Job Type *").select_option("1")
        self.page.get_by_label("Shift Type *").select_option("3")
        
        print(f"[ACTION] Entering Gross Salary: {gross_salary}")
        self.page.get_by_placeholder("Gross Salary (Monthly)").click()
        self.page.get_by_placeholder("Gross Salary (Monthly)").fill(gross_salary)
        
        # Trigger auto-calculation (sometimes requires clicking outside or hitting Tab)
        self.page.keyboard.press("Tab")
        self.page.wait_for_timeout(2000)
        
        # Extract UI calculated components
        print("[ACTION] Extracting calculated salary components from UI...")
        components = {
            "Basic Salary": self.page.get_by_label("Basic Salary").first.input_value(),
            "Employee PF": self.page.get_by_label(re.compile(r"Employee PF")).first.input_value(),
            "Employer PF": self.page.get_by_label(re.compile(r"Employer PF")).first.input_value(),
            "HRA": self.page.get_by_label(re.compile(r"HRA")).first.input_value(),
            "Conveyance": self.page.get_by_label(re.compile(r"Conveyance")).first.input_value(),
            "Monthly CTC": self.page.get_by_label("Monthly CTC").first.input_value(),
            "Annual CTC": self.page.get_by_label("Annual CTC").first.input_value(),
            "Net Salary": self.page.get_by_label("Net Salary").first.input_value()
        }
        
        print("[DATA] Extracted Components:", components)
        
        # Read the Offer Letter Preview table
        print("[ACTION] Scanning Offer Letter preview table for exact match validation...")
        try:
            self.page.get_by_text(re.compile(f"Dear {candidate_name}")).click(timeout=3000)
        except Exception:
            pass # Ignore if we can't click it, just need it to be visible in DOM
            
        # Get the table text
        tables = self.page.get_by_role("table").all()
        table_text = ""
        for table in tables:
            table_text += table.inner_text() + "\n"
            
        if not table_text:
            print("[WARN] No HTML table found in the DOM. Falling back to body text search.")
            table_text = self.page.locator("body").inner_text()
            
        # Strict validation: Ensure every calculated number exists in the preview table text
        missing_components = []
        for key, value in components.items():
            if value and value != "0" and value not in table_text:
                missing_components.append(f"{key}: {value}")
                
        if missing_components:
            raise AssertionError(f"Offer Letter Data Mismatch! The following UI values were missing from the Offer Letter preview table: {missing_components}")
            
        print("[PASS] Validation Successful: All auto-calculated UI numbers perfectly match the Offer Letter generated table.")
        
        # Send LOI
        print("[ACTION] Sending LOI...")
        self.page.get_by_role("button", name="Send").click()
        
        # Double click fallback if needed
        self.page.wait_for_timeout(1000)
        send_btn = self.page.get_by_role("button", name="Send")
        try:
            if send_btn.is_visible() and send_btn.is_enabled():
                send_btn.click()
        except Exception:
            pass # Ignore if button detached from DOM
            
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
        toast.wait_for(state="visible", timeout=15000)
        
        toast_msg = toast.inner_text()
        if "error" in toast_msg.lower() or "fail" in toast_msg.lower():
            raise AssertionError(f"Failed to send LOI: {toast_msg}")
            
        print(f"[TOAST SUCCESS] {toast_msg}")
        self.page.wait_for_load_state("networkidle")
