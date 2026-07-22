import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetProcurementPage(BasePage):
    NEW_PROCUREMENT_BTN = "role=button[name='New Procurement']"
    NEXT_BTN = "role=button[name='Next']"
    CREATE_BTN = "role=button[name='Create']"
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_procurement(self):
        logger.info("Navigating to Asset Procurement page")
        self.page.goto(f"{settings.BASE_URL}/asset-procurement")
        self.page.wait_for_load_state("networkidle")

    def click_new_procurement(self):
        self.click(self.NEW_PROCUREMENT_BTN)

    def fill_step1_details(self, vendor_label: str = None, branch_label: str = None, company_label: str = None, invoice_no: str = None, purchase_date: str = None, amount_before_gst: str = None, gst_amount: str = None):
        if vendor_label:
            logger.info(f"Selecting vendor: {vendor_label}")
            self.page.get_by_label("Vendor", exact=False).select_option(label=vendor_label)
            
        if branch_label:
            logger.info(f"Selecting branch: {branch_label}")
            self.page.get_by_label("Branch", exact=False).select_option(label=branch_label)
            
        if company_label:
            logger.info(f"Selecting company: {company_label}")
            self.page.get_by_label("Payroll Company", exact=False).select_option(label=company_label)
            
        if invoice_no:
            self.page.get_by_label("Invoice No.", exact=False).fill(invoice_no)
            
        if purchase_date:
            self.page.get_by_label("Purchase Date", exact=False).fill(purchase_date)
            
        if amount_before_gst:
            self.page.get_by_label("Amount Before GST", exact=False).fill(amount_before_gst)
            
        if gst_amount:
            self.page.get_by_label("GST Amount", exact=False).fill(gst_amount)

    def click_next(self):
        self.click(self.NEXT_BTN)
        self.page.wait_for_timeout(1000)

    def fill_step2_item(self, index: int, category_label: str = None, sub_category_label: str = None, brand: str = None, model: str = None, quantity: str = None, price: str = None, gst: str = None):
        # Locate elements dynamically within step 2 dialog
        dialog = self.page.locator("[role='dialog']")
        
        if category_label:
            logger.info(f"Selecting item category: {category_label}")
            # Category select is the first select in Step 2 or labeled Category
            dialog.get_by_label("Category", exact=False).nth(index).select_option(label=category_label)
            self.page.wait_for_timeout(500)
            
        if sub_category_label:
            logger.info(f"Selecting item subcategory: {sub_category_label}")
            dialog.get_by_label("Sub Category", exact=False).nth(index).select_option(label=sub_category_label)
            self.page.wait_for_timeout(500)
            
        if brand:
            dialog.get_by_placeholder("Enter Brand", exact=False).nth(index).fill(brand)
            
        if model:
            dialog.get_by_placeholder("Enter Model Name", exact=False).nth(index).fill(model)
            
        if quantity:
            dialog.get_by_placeholder("Enter Quantity", exact=False).nth(index).fill(quantity)
            
        if price:
            dialog.get_by_placeholder("Enter Price", exact=False).nth(index).fill(price)
            
        if gst:
            dialog.get_by_placeholder("Enter GST", exact=False).nth(index).fill(gst)

    def click_create(self):
        self.click(self.CREATE_BTN)
        
    def click_cancel(self):
        self.click(self.CANCEL_BTN)

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
