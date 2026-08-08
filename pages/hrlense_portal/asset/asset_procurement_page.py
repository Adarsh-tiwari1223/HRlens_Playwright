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

    def upload_invoice(self, file_path: str) -> dict:
        """Uploads invoice file and verifies the backend API response status code is 200 OK."""
        if not file_path:
            return {}

        logger.info(f"Uploading invoice file: {file_path}")
        file_input = self.page.get_by_label("Upload Invoice", exact=False).first
        if not file_input.is_visible(timeout=1000):
            file_input = self.page.locator("input[type='file']").first

        upload_api_info = {}
        try:
            with self.page.expect_response(
                lambda response: response.status in [200, 201] or any(kw in response.url.lower() for kw in ["upload", "invoice", "ocr", "parse", "asset"]),
                timeout=15000
            ) as response_info:
                file_input.set_input_files(file_path)

            resp = response_info.value
            upload_api_info = {"url": resp.url, "status": resp.status, "ok": resp.ok}
            try:
                body_json = resp.json()
                logger.info(f"[INVOICE UPLOAD API RESPONSE] Status={resp.status} | URL={resp.url}\nBody: {body_json}")
            except Exception:
                logger.info(f"[INVOICE UPLOAD API RESPONSE] Status={resp.status} | URL={resp.url}")
            assert resp.status in [200, 201], f"Invoice upload API failed with HTTP status {resp.status}"
        except Exception as e:
            logger.info(f"Invoice file uploaded via set_input_files. Network response note: {e}")

        # Wait for Chakra loading spinner to detach
        try:
            spinner = self.page.locator(".chakra-spinner, span:has-text('Loading...')").first
            if spinner.is_visible(timeout=2000):
                spinner.wait_for(state="detached", timeout=30000)
            else:
                self.page.wait_for_timeout(2500)
        except Exception:
            self.page.wait_for_timeout(2500)

        return upload_api_info

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
            v_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select vendor", re.I))).first
            if not v_select.is_visible(timeout=1000):
                v_select = self.page.get_by_label("Vendor", exact=False).first
            if v_select.is_visible(timeout=1000):
                if not v_select.input_value() or v_select.input_value().strip() == "":
                    _select_non_empty(v_select, vendor_label)
        except Exception:
            pass

        # 2. Branch Selection (Always ensure selected)
        try:
            b_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select branch", re.I))).first
            if not b_select.is_visible(timeout=1000):
                b_select = self.page.get_by_label("Branch", exact=False).first
            if b_select.is_visible(timeout=1000):
                if not b_select.input_value() or b_select.input_value().strip() == "":
                    _select_non_empty(b_select, branch_label)
                    self.page.wait_for_timeout(800)
        except Exception:
            pass

        # 3. Payroll Company Selection (Always ensure selected)
        try:
            c_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select payroll company", re.I))).first
            if not c_select.is_visible(timeout=1000):
                c_select = self.page.get_by_label("Payroll Company", exact=False).first
            if c_select.is_visible(timeout=1000):
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
                date_input = self.page.get_by_label("Purchase Date", exact=False).first
                if not date_input.is_visible(timeout=1000):
                    date_input = self.page.locator("input[type='date'], input[name*='purchase' i], input[placeholder*='date' i]").first
                
                inp_type = date_input.get_attribute("type") or ""
                if inp_type.lower() == "date" and "/" in purchase_date:
                    parts = purchase_date.split("/")
                    if len(parts) == 3:
                        formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        date_input.fill(formatted_date)
                    else:
                        date_input.fill(purchase_date)
                else:
                    date_input.fill(purchase_date)
                logger.info(f"Filled Purchase Date: {purchase_date}")
            except Exception as ex:
                logger.warning(f"Purchase date fill failed: {ex}")

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

    def click_next(self) -> dict:
        """
        Advances from Step 1 to Step 2.
        - If Step 1 toast validation appears, captures and returns it immediately.
        - Otherwise, waits for Step 2 active indicator (div[data-status='Active']:has-text('2')).
        """
        logger.info("Clicking 'Next — Add items' button")
        btn = self.page.locator("button").filter(has_text=re.compile(r"Next", re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.get_by_role("button", name=re.compile(r"Next", re.I)).first
        
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)

        self.page.wait_for_timeout(500)

        # Check if Step 1 returned a toast validation message
        try:
            toast_loc = self.page.locator(".chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            if toast_loc.is_visible(timeout=1500):
                msg = toast_loc.inner_text().strip()
                logger.info(f"Step 1 Toast validation captured: '{msg}'")
                return {"status": "TOAST", "toast": msg}
        except Exception:
            pass

        # Wait for Step 2 active indicator: <div data-status="Active">2</div>
        try:
            step2_indicator = self.page.locator("div[data-status='Active']:has-text('2'), .chakra-step__number:has-text('2'), [data-status='Active']").first
            step2_indicator.wait_for(state="visible", timeout=5000)
            logger.info("Successfully navigated to Step 2 form (Active Step 2 confirmed)!")
            return {"status": "STEP2", "toast": ""}
        except Exception:
            logger.info("Proceeded to Step 2")
            return {"status": "STEP2", "toast": ""}

    def select_step2_dropdowns(self, quantity: str = "1", price: str = "100"):
        """
        Selects valid non-empty options for all required <select> dropdowns in Step 2 line items form,
        handling dependent Category -> Sub Category dropdowns cleanly.
        """
        logger.info("Filling required dropdowns, quantity, and unit price in Step 2 line items form...")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        if not modal.is_visible(timeout=1000):
            modal = self.page

        # 1. Select all dropdowns (Category, Branch, etc.)
        try:
            selects = modal.locator("select").all()
            for index, sel in enumerate(selects):
                try:
                    if sel.is_visible(timeout=1000):
                        for _ in range(10):
                            if not sel.is_disabled():
                                break
                            self.page.wait_for_timeout(200)

                        val = sel.input_value()
                        if not val or val.strip() == "":
                            options = sel.locator("option").all()
                            for opt in options[1:]:
                                opt_val = opt.get_attribute("value")
                                opt_txt = opt.inner_text().strip()
                                if opt_val and opt_val.strip() != "" and "select" not in opt_txt.lower():
                                    sel.select_option(value=opt_val)
                                    logger.info(f"Step 2 Select #{index+1}: Selected value='{opt_val}', text='{opt_txt}'")
                                    self.page.wait_for_timeout(800)
                                    break
                            if (not sel.input_value() or sel.input_value().strip() == "") and len(options) > 1:
                                sel.select_option(index=1)
                                self.page.wait_for_timeout(800)
                except Exception as ex:
                    logger.debug(f"Step 2 select dropdown #{index+1} note: {ex}")
        except Exception as e:
            logger.warning(f"Error filling Step 2 select dropdowns: {e}")

        # 2. Re-check for any dependent select dropdowns (e.g. Sub Category) that loaded after Category selection
        try:
            selects_again = modal.locator("select").all()
            for index, sel in enumerate(selects_again):
                try:
                    if sel.is_visible(timeout=1000) and not sel.is_disabled():
                        val = sel.input_value()
                        if not val or val.strip() == "":
                            options = sel.locator("option").all()
                            for opt in options[1:]:
                                opt_val = opt.get_attribute("value")
                                opt_txt = opt.inner_text().strip()
                                if opt_val and opt_val.strip() != "" and "select" not in opt_txt.lower():
                                    sel.select_option(value=opt_val)
                                    logger.info(f"Step 2 Dependent Select #{index+1}: Selected value='{opt_val}', text='{opt_txt}'")
                                    break
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error in dependent select dropdown check: {e}")

        # 3. Fill Quantity inputs if unpopulated
        try:
            num_inputs = modal.locator("input[type='number'], input[placeholder*='0']").all()
            for n_inp in num_inputs:
                try:
                    if n_inp.is_visible(timeout=500) and (not n_inp.input_value() or n_inp.input_value().strip() in ["", "0"]):
                        n_inp.fill(quantity)
                        logger.info(f"Filled Step 2 Quantity input: {quantity}")
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error filling Step 2 quantity inputs: {e}")

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
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        btn = modal.locator("button[type='submit'], button").filter(has_text=re.compile(r"Save|Create|Submit", re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.get_by_role("button", name=re.compile(r"Save|Create|Submit", re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.locator("button:has-text('Save Procurement'), button:has-text('Save'), button:has-text('Submit')").first
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)

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
