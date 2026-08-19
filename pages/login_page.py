import logging
from pages.base_page import BasePage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)


class LoginPage(BasePage):

    def _fill_email(self, email: str):
        try:
            elem = self.page.locator("input[type='email'], input[name='email' i], input[placeholder*='email' i]").first
            if elem.is_visible(timeout=2000):
                elem.fill(email)
                return
        except Exception:
            pass
        self.page.get_by_label("Email").fill(email)

    def _fill_password(self, password: str):
        try:
            elem = self.page.locator("input[type='password'], input[name='password' i]").first
            if elem.is_visible(timeout=2000):
                elem.fill(password)
                return
        except Exception:
            pass
        self.page.get_by_label("Password").fill(password)

    def login(self, email: str, password: str):
        logger.info(f"[UI] Log In As               : {email}")
        try:
            self.page.wait_for_selector("input, label:has-text('Email')", timeout=15000)
        except Exception:
            pass

        captured_api_events = []

        def _on_response(response):
            try:
                url_lower = response.url.lower()
                if "api" in url_lower or "auth" in url_lower or "login" in url_lower or "token" in url_lower:
                    status = response.status
                    try:
                        body_snippet = response.text()[:500]
                    except Exception:
                        body_snippet = "<binary/unreadable>"

                    captured_api_events.append({
                        "type": "RESPONSE",
                        "url": response.url,
                        "status": status,
                        "body": body_snippet
                    })
                    if status >= 400:
                        logger.error(f"[LOGIN API ERROR] Status {status} | URL: {response.url}\nPayload/Response: {body_snippet}")
                    else:
                        logger.info(f"[LOGIN API SUCCESS] Status {status} | URL: {response.url}")
            except Exception:
                pass

        def _on_request_failed(request):
            try:
                url_lower = request.url.lower()
                if "api" in url_lower or "auth" in url_lower or "login" in url_lower or "token" in url_lower:
                    failure_text = request.failure or "CORS/Network error"
                    captured_api_events.append({
                        "type": "REQUEST_FAILED",
                        "url": request.url,
                        "status": "FAILED/CORS",
                        "body": str(failure_text)
                    })
                    logger.error(f"[LOGIN API CORS/NETWORK FAILURE] URL: {request.url} | Error: {failure_text}")
            except Exception:
                pass

        self.page.on("response", _on_response)
        self.page.on("requestfailed", _on_request_failed)

        self._fill_email(email)
        self._fill_password(password)

        try:
            self.page.get_by_role("button", name="Login").click()
        except Exception as click_err:
            logger.error(f"[UI] Login button click error: {click_err}")

        # Wait for redirect away from /login
        login_succeeded = False
        try:
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=12000)
            self.page.wait_for_load_state("domcontentloaded")
            login_succeeded = True
            logger.info(f"[UI] Logged In As            : {email}")
        except Exception:
            login_succeeded = ("/login" not in self.page.url)

        try:
            self.page.remove_listener("response", _on_response)
            self.page.remove_listener("requestfailed", _on_request_failed)
        except Exception:
            pass

        if not login_succeeded:
            # Capture any visible UI toast/error message
            toast_text = ""
            try:
                alert = self.page.locator(".chakra-toast, [role='alert'], .chakra-alert").first
                if alert.is_visible(timeout=1500):
                    toast_text = alert.inner_text().strip()
            except Exception:
                pass

            api_summary_lines = []
            for ev in captured_api_events:
                api_summary_lines.append(f"  • [{ev['type']}] Status: {ev['status']} | URL: {ev['url']}\n    Response: {ev['body']}")

            api_report = "\n".join(api_summary_lines) if api_summary_lines else "  • No API response captured (Network blocked/CORS)."

            error_message = (
                f"\n{'='*60}\n"
                f"[AUTHENTICATION FAILED] User '{email}' failed to log in.\n"
                f"Browser remained on: {self.page.url}\n"
                f"UI Toast/Error Message: '{toast_text or '<None>'}'\n"
                f"Backend API Diagnostics:\n{api_report}\n"
                f"{'='*60}\n"
            )
            logger.error(error_message)
            raise AssertionError(error_message)





    def click_login(self):
        self.page.get_by_role("button", name="Login").click()

    def click_forgot_password(self):
        self.page.get_by_text("Forgot Password?").click()

    def click_send_otp(self):
        self.page.get_by_role("button", name="Send OTP").click()

    def is_email_required_visible(self) -> bool:
        return self.page.get_by_text("Email is required").is_visible()

    def is_password_required_visible(self) -> bool:
        return self.page.get_by_text("Password is required").is_visible()

    def is_invalid_creds_visible(self) -> bool:
        import re
        self.page.wait_for_timeout(2000)
        try:
            # First check standard Chakra toast containers
            toast_loc = self.page.locator("#chakra-toast-manager-top-right, .chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            if toast_loc.is_visible(timeout=2000):
                txt = toast_loc.inner_text().strip()
                logger.info(f"Discovered authentication error toast: '{txt}'")
                return True
        except Exception:
            pass

        # Check all visible text elements for authentication error keywords
        try:
            elements = self.page.locator("p, div, span, label, [role='alert']").all()
            for el in elements:
                try:
                    if el.is_visible():
                        t = el.inner_text().strip()
                        if t and len(t) < 150 and any(k in t.lower() for k in ["invalid", "incorrect", "failed", "unauthorized", "wrong", "error", "not match"]):
                            logger.info(f"Discovered authentication error element text: '{t}'")
                            return True
                except Exception:
                    pass
        except Exception:
            pass

        return False

    def is_otp_email_required_visible(self) -> bool:
        return self.page.get_by_text("Please enter your email", exact=True).is_visible()

    def is_login_success_visible(self) -> bool:
        try:
            expect(self.page.get_by_text("Loggedin Successfully")).to_be_visible()
            return True
        except:
            return False


