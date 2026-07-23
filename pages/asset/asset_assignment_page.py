import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetAssignmentPage(BasePage):
    ASSIGN_ASSET_BTN = "role=button[name='Assign Asset']"
    SUBMIT_ASSIGNMENT_BTN = "role=button[name='Assign Asset']" # Form submit button
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_assignment(self):
        logger.info("Navigating to Asset Assignment page")
        self.page.goto(f"{settings.BASE_URL}/asset-assignment")
        self.page.wait_for_load_state("domcontentloaded")

    def click_assign_asset(self):
        self.page.locator(self.ASSIGN_ASSET_BTN).first.wait_for(state="visible", timeout=10000)
        self.page.locator(self.ASSIGN_ASSET_BTN).first.click()
        self.page.locator("[role='dialog'][aria-modal='true']").wait_for(state="visible", timeout=10000)

    def fill_assignment_details(self, employee_name: str, category: str, sub_category: str, asset_name_or_code: str = None, expected_return_date: str = None, remarks: str = None):
        logger.info(f"Filling assignment details: Employee={employee_name}, Category={category}, SubCategory={sub_category}")
        
        # Employee Search Search input
        emp_search = self.page.get_by_placeholder("Search employee name…")
        emp_search.fill(employee_name)
        self.page.wait_for_timeout(1000)
        # Select first matching result from suggestion popover/portal
        self.page.locator(".chakra-portal, [role='listbox']").get_by_text(employee_name, exact=False).first.click()
        
        # Category dropdown
        import re
        self.page.get_by_label("Category*", exact=True).select_option(label=category)
        self.page.wait_for_timeout(500)
        
        # Sub Category dropdown
        self.page.get_by_label("Sub Category*", exact=True).select_option(label=sub_category)
        self.page.wait_for_timeout(1000) # Wait for assets list to populate
        
        # Assets selector custom menu dropdown
        trigger_btn = self.page.get_by_role("button", name="Select assets to assign")
        trigger_btn.wait_for(state="visible", timeout=5000)
        trigger_btn.click()
        self.page.wait_for_timeout(500)
        
        if asset_name_or_code:
            # Select the option containing the asset name or code
            self.page.get_by_role("menuitem", name=re.compile(asset_name_or_code, re.IGNORECASE)).first.click()
        else:
            # Fallback: Select the first available menuitem
            self.page.get_by_role("menuitem").first.click()
            
        # Expected Return Date
        if expected_return_date:
            self.page.locator("input[type='date']").fill(expected_return_date)
            
        # Remarks
        if remarks:
            self.page.get_by_placeholder("e.g. Assigned during").fill(remarks)

    def click_submit_assignment(self):
        # We need to click the submit button inside the dialog drawer
        dialog = self.page.locator("[role='dialog'][aria-modal='true']")
        dialog.locator(self.SUBMIT_ASSIGNMENT_BTN).click()

    def click_cancel(self):
        self.click(self.CANCEL_BTN)

    def assign_requested_asset(self, employee_name: str, asset_code: str = None):
        import re
        logger.info(f"Assigning requested asset to employee: {employee_name}")
        # Click Requested Assignment tab
        self.page.get_by_role("tab", name="Requested Assignment").click()
        self.page.wait_for_timeout(2000)
        
        # Locate the row containing employee's request and click its action button
        row = self.page.get_by_role("row").filter(has_text=employee_name).first
        row.get_by_role("button").click()
        self.page.wait_for_timeout(1000)
        
        # Click "Assign Requested Asset" from the menu
        self.page.get_by_text("Assign Requested Asset").click()
        self.page.wait_for_timeout(1500)
        
        # Click the "Available Assets* Select" trigger
        self.page.locator("div").filter(has_text=re.compile(r"^Available Assets\*")).click()
        self.page.wait_for_timeout(1000)
        
        # Select the asset
        portal = self.page.locator(".chakra-portal")
        if asset_code:
            portal.get_by_text(asset_code, exact=False).first.click()
        else:
            portal.get_by_text("ASSET-LAP-", exact=False).first.click()
        self.page.wait_for_timeout(500)
            
        # Click "Assign Asset" button in form dialog
        self.page.get_by_role("button", name="Assign Asset").click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
