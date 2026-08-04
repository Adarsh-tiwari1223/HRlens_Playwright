import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetProcurementPage(BasePage):

    def navigate_to_asset_procurement(self):
        """Navigates to Asset Procurement page via side menu or direct URL."""
        logger.info("Navigating to Asset Procurement page")
        try:
            asset_link = self.page.get_by_role("link", name="Asset", exact=True).first
            if asset_link.is_visible(timeout=3000):
                asset_link.click()
                self.page.wait_for_timeout(500)
                proc_link = self.page.get_by_role("link", name="• Asset Procurement").first
                if proc_link.is_visible(timeout=3000):
                    proc_link.click()
                    self.page.wait_for_load_state("domcontentloaded")
                    return
        except Exception:
            pass

        # Fallback to direct navigation
        self.page.goto(f"{settings.BASE_URL}/asset-procurement")
        self.page.wait_for_load_state("domcontentloaded")

    def click_new_procurement(self):
        """Clicks 'New Procurement' button to open procurement form wizard."""
        btn = self.page.get_by_role("button", name="New Procurement").first
        if not btn.is_visible():
            btn = self.page.locator("button:has-text('New Procurement')").first
        btn.click()
        self.page.wait_for_timeout(1000)

    def upload_invoice(self, file_path: str):
        """Uploads invoice file (PDF/JPG/PNG) and waits for Chakra loading spinner to detach/hide."""
        if not file_path:
            return

        logger.info(f"Uploading invoice file: {file_path}")
        try:
            file_input = self.page.get_by_label("Upload Invoice", exact=False).first
            if not file_input.is_visible():
                file_input = self.page.locator("input[type='file']").first
            file_input.set_input_files(file_path)
            
            # Wait for Chakra loading spinner to appear then detach
            try:
                spinner = self.page.locator(".chakra-spinner, span:has-text('Loading...')").first
                if spinner.is_visible(timeout=3000):
                    spinner.wait_for(state="detached", timeout=30000)
                else:
                    self.page.wait_for_timeout(2500)
            except Exception:
                self.page.wait_for_timeout(2500)
        except Exception as e:
            logger.warning(f"Invoice file upload failed or optional: {e}")

    def fill_step1_details(
        self,
        vendor_label: str = None,
        branch_label: str = None,
        company_label: str = None,
        invoice_no: str = None,
        purchase_date: str = None,
        amount_before_gst: str = None,
        gst_amount: str = None,
        invoice_file_path: str = None
    ):
        """
        Fills Step 1 procurement details.
        When an invoice is uploaded, ONLY selects Branch and Payroll Company if unselected,
        and strictly preserves all prefilled textboxes without editing.
        """
        if invoice_file_path:
            self.upload_invoice(invoice_file_path)

        def _select_non_empty(select_locator, label_val=None):
            if label_val:
                try:
                    select_locator.select_option(label=label_val)
                    if select_locator.input_value() and select_locator.input_value().strip() != "":
                        return
                except Exception:
                    pass
            # Find first non-empty value option
            for _ in range(5):
                try:
                    options = select_locator.locator("option").all()
                    for opt in options[1:]:
                        val = opt.get_attribute("value")
                        txt = opt.inner_text().strip()
                        if val and val.strip() != "" and "select" not in txt.lower():
                            select_locator.select_option(value=val)
                            return
                    if len(options) > 1:
                        select_locator.select_option(index=1)
                        if select_locator.input_value() and select_locator.input_value().strip() != "":
                            return
                except Exception:
                    pass
                self.page.wait_for_timeout(500)

        # 1. Vendor Selection (Select only if unselected)
        try:
            v_select = self.page.get_by_label("Vendor*", exact=True)
            if not v_select.input_value() or v_select.input_value().strip() == "":
                _select_non_empty(v_select, vendor_label)
        except Exception:
            pass

        # 2. Branch Selection (Always ensure selected)
        try:
            b_select = self.page.get_by_label("Branch*", exact=True)
            if not b_select.input_value() or b_select.input_value().strip() == "":
                _select_non_empty(b_select, branch_label)
                self.page.wait_for_timeout(800)
        except Exception:
            pass

        # 3. Payroll Company Selection (Always ensure selected)
        try:
            c_select = self.page.get_by_label("Payroll Company*", exact=True)
            if not c_select.input_value() or c_select.input_value().strip() == "":
                _select_non_empty(c_select, company_label)
        except Exception:
            pass

        # If invoice was uploaded, DO NOT edit prefilled textboxes!
        if invoice_file_path:
            logger.info("Invoice uploaded — preserving all prefilled textboxes without editing.")
            return

        # Manual fallback fill ONLY if invoice was NOT uploaded:
        if invoice_no:
            try:
                inv_input = self.page.get_by_label("Invoice No.", exact=False).first
                if inv_input.is_visible() and not inv_input.input_value():
                    inv_input.fill(invoice_no)
            except Exception:
                pass

        if purchase_date:
            try:
                date_input = self.page.get_by_label("Purchase Date*", exact=True).first
                if date_input.is_visible() and not date_input.input_value():
                    date_input.fill(purchase_date)
            except Exception:
                pass

        if amount_before_gst:
            try:
                amt_div = self.page.locator("div").filter(has_text=re.compile(r"^Amount Before GST \(₹\)$")).locator("input").first
                if amt_div.is_visible() and not amt_div.input_value():
                    amt_div.fill(amount_before_gst)
            except Exception:
                pass

        if gst_amount:
            try:
                gst_div = self.page.locator("div").filter(has_text=re.compile(r"^GST Amount \(₹\)$")).locator("input").first
                if gst_div.is_visible() and not gst_div.input_value():
                    gst_div.fill(gst_amount)
            except Exception:
                pass

    def click_next(self):
        """Advances from Step 1 to Step 2 (Add Items)."""
        btn = self.page.get_by_role("button", name=re.compile(r"Next", re.I)).first
        if not btn.is_visible():
            btn = self.page.locator("button:has-text('Next')").first
        btn.click()
        self.page.wait_for_timeout(1000)

    def fill_step2_item(
        self,
        index: int = 0,
        category_label: str = None,
        sub_category_label: str = None,
        brand: str = None,
        model: str = None,
        quantity: str = "1",
        price: str = "100",
        gst: str = None
    ):
        """Fills item specifications in Step 2 dialog."""
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page

        # Category Select
        try:
            cat_select = dialog.get_by_label("Category", exact=True).nth(index)
            if category_label:
                cat_select.select_option(label=category_label)
            else:
                cat_select.select_option(index=1)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

        # Sub Category Select
        try:
            sub_select = dialog.get_by_label("Sub category", exact=True).nth(index)
            if sub_category_label:
                sub_select.select_option(label=sub_category_label)
            else:
                sub_select.select_option(index=1)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

        # Brand
        if brand:
            try:
                dialog.get_by_placeholder("e.g. Dell", exact=False).nth(index).fill(brand)
            except Exception:
                pass

        # Model
        if model:
            try:
                dialog.get_by_placeholder("e.g. XPS", exact=False).nth(index).fill(model)
            except Exception:
                pass

        # Quantity
        if quantity:
            try:
                dialog.get_by_placeholder("0", exact=False).nth(index).fill(quantity)
            except Exception:
                pass

        # Price
        if price:
            try:
                dialog.get_by_placeholder("0.00", exact=False).nth(index).fill(price)
            except Exception:
                pass

    def click_create(self):
        """Saves procurement request."""
        btn = self.page.get_by_role("button", name=re.compile(r"Save|Create", re.I)).first
        if not btn.is_visible():
            btn = self.page.locator("button:has-text('Save Procurement'), button:has-text('Save')").first
        btn.click()

    def click_cancel(self):
        """Cancels procurement form."""
        btn = self.page.get_by_role("button", name="Cancel").first
        if not btn.is_visible():
            btn = self.page.locator("button:has-text('Cancel')").first
        btn.click()

    def inspect_and_log_step1_fields(self) -> dict[str, str]:
        """Inspects all Step 1 form fields after invoice upload and logs field-by-field status to terminal."""
        field_status = {}

        # 1. Vendor
        try:
            v_val = self.page.get_by_label("Vendor*", exact=True).input_value()
            field_status["Vendor"] = v_val if v_val and v_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Vendor"] = "NOT FOUND"

        # 2. Branch
        try:
            b_val = self.page.get_by_label("Branch*", exact=True).input_value()
            field_status["Branch"] = b_val if b_val and b_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Branch"] = "NOT FOUND"

        # 3. Payroll Company
        try:
            c_input = self.page.get_by_label("Company*", exact=False).first
            if not c_input.is_visible():
                c_input = self.page.locator("select[name*='company'], select[aria-label*='Company']").first
            c_val = c_input.input_value()
            field_status["Payroll Company"] = c_val if c_val and c_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Payroll Company"] = "NOT FOUND"

        # 4. Invoice No
        try:
            inv_val = self.page.get_by_label("Invoice No.", exact=False).first.input_value()
            field_status["Invoice No"] = inv_val if inv_val and inv_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Invoice No"] = "NOT FOUND"

        # 5. Purchase Date
        try:
            d_val = self.page.get_by_label("Purchase Date*", exact=True).first.input_value()
            field_status["Purchase Date"] = d_val if d_val and d_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Purchase Date"] = "NOT FOUND"

        # 6. Amount Before GST
        try:
            amt_val = self.page.locator("div").filter(has_text=re.compile(r"^Amount Before GST \(₹\)$")).locator("input").first.input_value()
            field_status["Amount Before GST"] = amt_val if amt_val and amt_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Amount Before GST"] = "NOT FOUND"

        # 7. GST Amount
        try:
            gst_val = self.page.locator("div").filter(has_text=re.compile(r"^GST Amount \(₹\)$")).locator("input").first.input_value()
            field_status["GST Amount"] = gst_val if gst_val and gst_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["GST Amount"] = "NOT FOUND"

        logger.info("\n" + "=" * 80)
        logger.info("INVOICE AUTO-FILL FORM FIELD INSPECTION REPORT")
        logger.info("=" * 80)
        for field, status in field_status.items():
            state_label = f"POPULATED ('{status}')" if status not in ["EMPTY", "NOT FOUND"] else f"[{status}]"
            logger.info(f"{field:<24} : {state_label}")
        logger.info("=" * 80 + "\n")

        print("\n" + "=" * 80)
        print("INVOICE AUTO-FILL FORM FIELD INSPECTION REPORT")
        print("=" * 80)
        for field, status in field_status.items():
            state_label = f"POPULATED ('{status}')" if status not in ["EMPTY", "NOT FOUND"] else f"[{status}]"
            print(f"{field:<24} : {state_label}")
        print("=" * 80 + "\n")

        return field_status

    def inspect_and_log_asset_line_items(self) -> list[dict]:
        """Reads and logs all prefilled asset line items (Item 1 to Item N) from Step 2 without editing values."""
        logger = logging.getLogger("hrlense")

        cards = self.page.locator(
            "//div[@role='group'][.//label[normalize-space()='Brand']]/ancestor::div[.//p[contains(.,'Line Total')]][1]"
        )

        count = cards.count()

        logger.info("\n" + "=" * 80)
        logger.info("ASSET LINE ITEM SUMMARY")
        logger.info("=" * 80)
        logger.info("Total Asset Items : %s", count)

        items_data = []

        for i in range(count):
            card = cards.nth(i)

            # Category
            try:
                cat_el = card.locator("select[aria-label*='Category'], select[name*='category']").first
                cat_text = cat_el.input_value().strip() if cat_el.is_visible() else "Hardware"
            except Exception:
                cat_text = "Hardware"

            # Sub Category
            try:
                sub_el = card.get_by_label("Sub category", exact=False).first
                if not sub_el.is_visible():
                    sub_el = card.locator("select[aria-label*='Sub'], select[name*='sub']").first
                sub_text = sub_el.input_value().strip() if sub_el.is_visible() else "<Empty>"
            except Exception:
                sub_text = "<Empty>"

            # Brand (Filter out placeholder 'e.g. Dell')
            try:
                b_in = card.get_by_label("Brand", exact=False).first
                brand_val = b_in.input_value().strip()
                if not brand_val or "e.g." in brand_val.lower():
                    brand_val = "<Empty>"
            except Exception:
                brand_val = "<Empty>"

            # Model no. (Filter out placeholder 'e.g. XPS')
            try:
                m_in = card.get_by_label("Model no.", exact=False).first
                model_val = m_in.input_value().strip()
                if not model_val or "e.g." in model_val.lower():
                    model_val = "<Empty>"
            except Exception:
                model_val = "<Empty>"

            # Quantity
            try:
                q_in = card.get_by_label("Quantity", exact=False).first
                qty_val = q_in.input_value().strip()
            except Exception:
                qty_val = "<Empty>"

            # Unit Price
            try:
                p_in = card.get_by_label("Unit price (₹)", exact=False).first
                price_val = p_in.input_value().strip()
            except Exception:
                price_val = "<Empty>"

            # Line Total
            try:
                line_total = card.locator("text=/Line Total/i").first.inner_text().strip()
            except Exception:
                line_total = "Line Total: N/A"

            logger.info("-" * 80)
            logger.info("Asset Item        : %s", i + 1)
            logger.info("Category          : %s", cat_text or "Hardware")
            logger.info("Sub Category      : %s", sub_text or "<Empty>")
            logger.info("Brand             : %s", brand_val)
            logger.info("Model No.         : %s", model_val)
            logger.info("Quantity          : %s", qty_val)
            logger.info("Unit Price (₹)    : %s", price_val)
            logger.info("Line Total        : %s", line_total)

            items_data.append({
                "index": i + 1,
                "category": cat_text,
                "sub_category": sub_text,
                "brand": brand_val,
                "model": model_val,
                "quantity": qty_val,
                "unit_price": price_val,
                "line_total": line_total
            })

        logger.info("=" * 80)
        logger.info("Completed reading %s asset line item(s).", count)
        logger.info("=" * 80 + "\n")

        return items_data

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast("#chakra-toast-manager-top-right")
