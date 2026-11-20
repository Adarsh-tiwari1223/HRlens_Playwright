"""
Advanced Test Suite for Induction Module (Post-Fix Verification).
Covers 3 Critical Scenarios:
1. Scenario 1: Candidate Portal Real Experience (/induction)
   - Checks candidate view under 'adarsh' (TEK Inspirations LLC).
   - Validates /api/Induction/status and background APIs.
   - Inspects whether company-specific vs fallback hero banner loads.
2. Scenario 2: Sequence Number Overlap Across 2 Companies
   - Validates whether two distinct companies can use Sequence #1 in the same step.
   - Detects whether client-side validation is tab-wide or company-scoped.
3. Scenario 3: Multi-Company Selection in '+ Add Content' Modal
   - Selects 2 companies simultaneously.
   - Audits whether company_Id becomes null and how backend processes company_Ids.
"""

import os
import json
import logging
import pytest
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import Page, expect
from pages.hrlense_portal.master.master_induction_policy_page import MasterInductionPolicyPage
from pages.hrlense_portal.induction.induction_page import InductionPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.induction
class TestInductionThreeAdvancedScenarios:
    """Automated verification suite for the 3 advanced induction scenarios."""

    def test_scenario_1_candidate_portal_real_experience(self, admin_page):
        """
        Scenario 1: Candidate Portal Real Experience (/induction)
        - Uses authenticated persona (TEK Inspirations LLC / Development / Varanasi).
        - Navigates to /induction.
        - Audits /api/Induction/status and welcome slide banners.
        - Verifies no unhandled 500 or CORS failures occur.
        """
        candidate_page = admin_page
        captured_api_responses = []

        def on_response(response):
            url = response.url
            if "/api/" in url.lower():
                captured_api_responses.append({
                    "url": url,
                    "status": response.status,
                    "method": response.request.method
                })

        candidate_page.on("response", on_response)

        induction_page = InductionPage(candidate_page)
        logger.info("[SCENARIO 1] Navigating to Candidate Induction Portal: /induction...")
        induction_page.navigate_to_induction()
        candidate_page.wait_for_timeout(4000)

        # Check candidate URL
        curr_url = candidate_page.url
        logger.info(f"[SCENARIO 1] Current Candidate URL: {curr_url}")
        assert "/induction" in curr_url, f"Failed to load candidate induction portal! Current URL: {curr_url}"

        # 1. Audit /api/Induction/status API call
        status_calls = [r for r in captured_api_responses if "/api/induction/status" in r["url"].lower()]
        print("\n" + "=" * 80)
        print("         SCENARIO 1: CANDIDATE PORTAL API AUDIT (/induction)")
        print("=" * 80)
        print(f"  Candidate Account:        Admin / Software Developer (TEK Inspirations LLC)")
        print(f"  Candidate Portal URL:     {curr_url}")
        print(f"  Total API Calls Captured: {len(captured_api_responses)}")

        if status_calls:
            status_call = status_calls[-1]
            print(f"  /api/Induction/status:    HTTP {status_call['status']} ({'HEALTHY OK' if status_call['status'] == 200 else 'FAILED'})")
            assert status_call["status"] == 200, f"/api/Induction/status returned HTTP {status_call['status']}!"
        else:
            print("  /api/Induction/status:    Not triggered or already cached in session")

        # Check for any 500 errors across all APIs
        server_errors = [r for r in captured_api_responses if r["status"] >= 500]
        print(f"  Backend 500 Server Errors: {len(server_errors)} ({'NONE - ALL CLEAN' if len(server_errors) == 0 else [s['url'] for s in server_errors]})")
        assert len(server_errors) == 0, f"Found 500 server errors on candidate portal: {server_errors}"

        # 2. Inspect Candidate Welcome Slides & Background Banner
        has_welcome = induction_page.is_welcome_slide_visible()
        print(f"  Welcome Journey Visible:  {has_welcome}")

        # Extract all slide background images / images rendered
        slide_images = candidate_page.evaluate("""() => {
            const imgs = Array.from(document.querySelectorAll('img, [style*="background"]')).map(el => {
                const src = el.src || '';
                const style = el.getAttribute('style') || '';
                return { tag: el.tagName, src: src, style: style };
            });
            return imgs.filter(i => i.src.includes('banner') || i.style.includes('banner') || i.src.includes('.jpg'));
        }""")
        print(f"  Candidate Slide Banner Images Loaded: {json.dumps(slide_images, indent=2)}")

        # Advance through welcome slides if visible
        if has_welcome:
            logger.info("[SCENARIO 1] Advancing through candidate welcome slides...")
            induction_page.advance_welcome_slides(selected_guide="Sufi")
            candidate_page.wait_for_timeout(2000)

        # Verify Chapter View reached
        has_chapters = candidate_page.locator("div:has-text('CHAPTER PROGRESS'), div:has-text('% completed')").count() > 0
        print(f"  Interactive Chapter View: {'ACCESSIBLE & ACTIVE' if has_chapters else 'Welcome Slides Active'}")
        print("=" * 80 + "\n")

    def test_scenario_2_sequence_number_overlap_across_companies(self, admin_page):
        """
        Scenario 2: Multi-Company Sequence Overlap (Edit/Add Modal)
        - Opens '+ Add Content' modal in /master/induction-policy.
        - Checks existing Sequence #1 in Step 1.
        - Tests whether setting Sequence #1 for Company B is blocked
          by Company A's Sequence #1 due to tab-wide validation.
        """
        page = MasterInductionPolicyPage(admin_page)
        logger.info("[SCENARIO 2] Navigating to Master Induction Policy...")
        page.navigate_to_induction_policy()
        page.switch_to_step_content_tab()
        admin_page.wait_for_timeout(2000)

        # 1. Open '+ Add Content' Modal
        logger.info("[SCENARIO 2] Clicking '+ Add Content' button...")
        page.open_add_content_modal()
        admin_page.wait_for_timeout(2000)

        modal = admin_page.locator("div[role='dialog'], section[role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=6000)

        print("\n" + "=" * 80)
        print("   SCENARIO 2: SEQUENCE OVERLAP ACROSS COMPANIES AUDIT")
        print("=" * 80)

        # Check order/sequence input field
        order_input = modal.locator("input[type='number'], input[name*='order' i], input[placeholder*='order' i], input[placeholder*='sequence' i]").first
        assert order_input.is_visible(), "Sequence / Order number input not found in Add Content modal!"

        # Enter Sequence 1
        order_input.fill("1")
        admin_page.wait_for_timeout(500)

        # 2. Select Step 1
        step_select = modal.locator("select").filter(has=admin_page.locator("option:has-text('Step 1')")).first
        if step_select.is_visible():
            step_select.select_option(label="Step 1 · Company Profile")
            admin_page.wait_for_timeout(500)

        # 3. Target Audience: Select Company 'Adventa Tech Inc'
        comp_btn = modal.locator("div:has(> label:has-text('Company')) button[aria-haspopup='menu']").first
        if comp_btn.is_visible():
            comp_btn.click()
            admin_page.wait_for_timeout(500)
            chk = admin_page.locator("label.chakra-checkbox:has-text('Adventa Tech Inc')").first
            if chk.is_visible():
                chk.click()
                logger.info("[SCENARIO 2] Selected Company: 'Adventa Tech Inc'")
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)

        # 4. Fill dummy Title & Content
        title_input = modal.locator("input[type='text']").first
        if title_input.is_visible():
            title_input.fill("Adventa Tech Test Policy Sequence 1")

        content_area = modal.locator("textarea").first
        if content_area.is_visible():
            content_area.fill("Testing sequence number 1 for Adventa Tech Inc.")

        # Check validation errors on sequence
        errors = [e.inner_text().strip() for e in modal.locator(".chakra-form__error-message, [aria-invalid='true']").all() if e.inner_text().strip()]
        has_seq_error = any("already exists" in e.lower() or "sequence" in e.lower() or "order" in e.lower() for e in errors)

        print(f"  Target Step:              Step 1: Company Profile")
        print(f"  Selected Company:         Adventa Tech Inc")
        print(f"  Entered Sequence Number:  1")
        print(f"  Detected Form Errors:     {errors if errors else 'None'}")
        print(f"  Sequence Blocked?         {'YES -> TAB-WIDE SEQUENCE CONFLICT (BUG-IND-04)' if has_seq_error else 'NO -> Sequence Allowed for different company'}")
        print("=" * 80 + "\n")

        # Clean cancel modal
        cancel_btn = modal.locator("button:has-text('Cancel')").first
        if cancel_btn.is_visible():
            cancel_btn.click()
        else:
            admin_page.keyboard.press("Escape")
        admin_page.wait_for_timeout(1000)

    def test_scenario_3_multicompany_selection_in_add_content(self, admin_page):
        """
        Scenario 3: Multi-Company Selection in '+ Add Content' Modal
        - Opens '+ Add Content' modal.
        - Selects 2 companies simultaneously: 'TEK Inspirations LLC' AND 'Adventa Tech Inc'.
        - Intercepts network payload on submit to verify whether company_Id is null
          or company_Ids array is passed and accepted by backend.
        """
        captured_payloads = []

        def on_request(request):
            url = request.url
            if "/api/" in url.lower() and request.method in ["POST", "PUT"]:
                captured_payloads.append({
                    "url": url,
                    "method": request.method,
                    "body": request.post_data or "",
                    "content_type": request.headers.get("content-type", "")
                })

        admin_page.on("request", on_request)

        page = MasterInductionPolicyPage(admin_page)
        logger.info("[SCENARIO 3] Navigating to Master Induction Policy...")
        page.navigate_to_induction_policy()
        page.switch_to_step_content_tab()
        admin_page.wait_for_timeout(2000)

        # 1. Open '+ Add Content' Modal
        page.open_add_content_modal()
        admin_page.wait_for_timeout(2000)

        modal = admin_page.locator("div[role='dialog'], section[role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=6000)

        print("\n" + "=" * 80)
        print("   SCENARIO 3: MULTI-COMPANY SELECTION IN ADD CONTENT AUDIT")
        print("=" * 80)

        # 2. Select 2 Companies
        comp_btn = modal.locator("div:has(> label:has-text('Company')) button[aria-haspopup='menu']").first
        assert comp_btn.is_visible(), "Company dropdown button not found in modal!"
        comp_btn.click()
        admin_page.wait_for_timeout(600)

        chk1 = admin_page.locator("label.chakra-checkbox:has-text('TEK Inspirations LLC')").first
        chk2 = admin_page.locator("label.chakra-checkbox:has-text('Adventa Tech Inc')").first
        if chk1.is_visible():
            chk1.click()
            admin_page.wait_for_timeout(300)
        if chk2.is_visible():
            chk2.click()
            admin_page.wait_for_timeout(300)

        admin_page.keyboard.press("Escape")
        admin_page.wait_for_timeout(600)

        # 3. Enter Category, Title, Content, Order
        cat_input = modal.locator("input[placeholder*='Vision' i], input[placeholder*='category' i]").first
        if cat_input.is_visible():
            cat_input.fill("Corporate Policies")

        title_input = modal.locator("input[placeholder*='Branch' i], input[placeholder*='title' i]").first
        if title_input.is_visible():
            title_input.fill("Automated Multi-Company Test Policy")

        content_area = modal.locator("textarea").first
        if content_area.is_visible():
            content_area.fill("This is an automated test policy scoped to multiple companies.")

        order_input = modal.locator("input[type='number']").first
        if order_input.is_visible():
            order_input.fill("99")

        # Hide chatbot widget if floating
        admin_page.evaluate("() => { const b = document.querySelector('.ai-chatbot-wrapper'); if (b) b.style.display = 'none'; }")

        # 4. Click Submit / Create Content
        reqs_before = len(captured_payloads)
        submit_btn = modal.locator("button[type='submit']:has-text('Create Content'), button:has-text('Create Content'), button[type='submit']:has-text('Save')").first
        logger.info("[SCENARIO 3] Submitting modal with 2 companies selected...")
        submit_btn.click(force=True)
        admin_page.wait_for_timeout(4000)

        submit_reqs = captured_payloads[reqs_before:]
        print(f"  Selected Companies:       ['TEK Inspirations LLC', 'Adventa Tech Inc']")
        print(f"  Captured Submit Requests: {len(submit_reqs)}")

        if submit_reqs:
            for req in submit_reqs:
                print(f"\n  API ENDPOINT: [{req['method']}] {req['url']}")
                body = req['body']
                try:
                    parsed = json.loads(body)
                    print(f"  Payload JSON:\n{json.dumps(parsed, indent=4)}")
                    print(f"  company_Id value:         {parsed.get('company_Id')} ({'NULL (BUG DETECTED)' if parsed.get('company_Id') is None else 'POPULATED'})")
                    print(f"  company_Ids value:        {parsed.get('company_Ids')}")
                except Exception:
                    print(f"  Raw Payload: {body[:300]}")
        else:
            print("  ⚠️ No submit request captured! Checking validation errors:")
            errors = [e.inner_text().strip() for e in modal.locator(".chakra-form__error-message, [aria-invalid='true']").all() if e.inner_text().strip()]
            print(f"  Form Validation Errors:   {errors}")

        # Check toasts
        toasts = admin_page.evaluate("() => Array.from(document.querySelectorAll('.chakra-toast, .chakra-alert, [data-status]')).map(e => e.innerText.trim()).filter(Boolean)")
        print(f"  Toast Messages:           {toasts}")
        print("=" * 80 + "\n")

        # Clean cancel if modal still open
        if modal.is_visible():
            cancel_btn = modal.locator("button:has-text('Cancel')").first
            if cancel_btn.is_visible():
                cancel_btn.click()
            else:
                admin_page.keyboard.press("Escape")
        admin_page.wait_for_timeout(1000)
