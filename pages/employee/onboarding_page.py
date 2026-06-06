import re
from playwright.sync_api import Page

class OnboardingPage:
    def __init__(self, page: Page):
        self.page = page

    def navigate_to_onboarding(self):
        """Navigates to the Offers & Onboarding module."""
        print("[ACTION] Navigating to Offers & Onboarding...")
        # Note: 'Onbording' is misspelled in the UI based on the codegen trace
        self.page.get_by_role("link", name=re.compile(r"Offers & Onbording|Offers & Onboarding", re.IGNORECASE)).click()
        self.page.wait_for_load_state("networkidle")

    def open_verification_modal(self, candidate_name: str):
        """
        Locates the candidate row in the onboarding grid and clicks the action icon 
        to open the verification form.
        """
        print(f"[ACTION] Searching for candidate {candidate_name} in Onboarding grid...")
        row = self.page.get_by_role("row", name=re.compile(candidate_name, re.IGNORECASE))
        # The trace shows clicking an img (action icon) inside the row
        row.get_by_role("img").first.click()
        
        print("[ACTION] Checking document verification...")
        # Check the 'Verify Documents' checkbox
        self.page.locator("label span").first.click()
        self.page.get_by_role("button", name="Verify").click()
        self.page.wait_for_timeout(1000)

    def fill_verification_form_and_send(self, candidate_name: str, doj: str):
        """
        Fills out the mandatory fields for generating the final Offer/Appointment letter
        and sends it.
        """
        print("[ACTION] Filling Onboarding verification form...")
        
        # 1. Official Email
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', candidate_name)
        official_email = f"{safe_name}@tekinspirations.com"
        print(f"[DATA] Generating Official Email: {official_email}")
        self.page.get_by_placeholder("Enter official Email").fill(official_email)
        
        # 2. Designation (20 = probably some specific title based on trace)
        self.page.get_by_label("Designation *").select_option("20")
        
        # 3. DOJ
        self.page.get_by_placeholder("Select date of Joining").fill(doj)
        
        # 4. Business Process & Shift
        self.page.get_by_label("Business Process *").select_option("4")
        self.page.get_by_label("Shift *").select_option("3")
        
        # 5. Probation Period
        self.page.get_by_placeholder("Enter Probation Period").fill("03")
        
        # 6. Role Selection
        print("[ACTION] Assigning Role: HR Executive...")
        self.page.get_by_role("button", name="Select role").click()
        self.page.get_by_role("menuitem", name="HR Executive").click()
        # Click outside to close the dropdown if needed
        self.page.locator("body").click()
        
        # 7. Managers
        print("[ACTION] Assigning Manager and Team Lead...")
        self.page.get_by_placeholder("Select Manager...").fill("ritesh")
        self.page.get_by_text("Ritesh Singh").first.click()
        
        self.page.get_by_placeholder("Select Team Lead...").fill("ritesh")
        self.page.get_by_text("Ritesh Singh").first.click()
        
        # 8. Submit
        print("[ACTION] Clicking Verify & Send Offer Letter...")
        self.page.get_by_role("button", name="Verify & Send Offer Letter").click()
        
        # 9. Wait for toast and check for Network Error
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast, .Toastify__toast").first
        toast.wait_for(state="visible", timeout=15000)
        
        toast_msg = toast.inner_text().lower()
        print(f"[TOAST RESPONSE] {toast_msg}")
        
        if "error" in toast_msg or "fail" in toast_msg:
            raise AssertionError(f"Backend rejected verification: {toast_msg}")
            
        print("[PASS] Verification successful!")
        self.page.wait_for_load_state("networkidle")
