import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetMaintenancePage(BasePage):
    CREATE_MAINTENANCE_BTN = "role=button[name='Create Maintenance']"
    SUBMIT_CASE_BTN = "role=button[name='Create Case']"
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_maintenance(self):
        logger.info("Navigating to Asset Maintenance page")
        self.page.goto(f"{settings.BASE_URL}/asset-maintenance")
        self.page.wait_for_load_state("domcontentloaded")

    def click_create_maintenance(self):
        self.page.locator(self.CREATE_MAINTENANCE_BTN).wait_for(state="visible", timeout=10000)
        self.click(self.CREATE_MAINTENANCE_BTN)
        self.page.locator("[role='dialog'][aria-modal='true']").wait_for(state="visible", timeout=10000)

    def fill_maintenance_details(self, asset_code_or_name: str, issue_type: str, description: str = None, sent_date: str = None, expected_return: str = None, estimated_cost: str = None, remarks: str = None):
        logger.info(f"Filling maintenance details: Asset={asset_code_or_name}, Issue={issue_type}")
        
        # Asset Search input
        asset_input = self.page.get_by_placeholder("Search by asset code or name...")
        asset_input.fill(asset_code_or_name)
        self.page.wait_for_timeout(1000)
        # Click suggestion first item
        self.page.locator(".chakra-portal, [role='listbox']").get_by_text(asset_code_or_name, exact=False).first.click()
        
        # Issue Type
        self.page.get_by_label("Issue Type", exact=False).select_option(label=issue_type)
        
        # Issue Description
        if description:
            self.page.get_by_placeholder("Describe the issue in detail...").fill(description)
            
        # Sent Date (first date input)
        if sent_date:
            self.page.locator("input[type='date']").first.fill(sent_date)
            
        # Expected Return Date (second date input)
        if expected_return:
            self.page.locator("input[type='date']").nth(1).fill(expected_return)
            
        # Estimated Cost
        if estimated_cost:
            self.page.get_by_placeholder("0").fill(estimated_cost)
            
        # Remarks
        if remarks:
            self.page.get_by_placeholder("e.g. Sent to authorized service center").fill(remarks)

    def click_submit_case(self):
        self.click(self.SUBMIT_CASE_BTN)

    def click_cancel(self):
        self.click(self.CANCEL_BTN)

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
