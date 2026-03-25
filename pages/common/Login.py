from pages.base_page import BasePage
from locators.modules.login_locators import LoginLocators


class LoginPage(BasePage):
    def login(self, username: str, password: str):
        self.fill(LoginLocators.EMAIL, username)
        self.fill(LoginLocators.PASSWORD, password)
        self.click(LoginLocators.LOGIN_BUTTON)

    def click_login_button(self):
        return self.click(LoginLocators.LOGIN_BUTTON)
    
    def is_email_error_visible(self) -> bool:
        return self.is_visible(LoginLocators.EMAIL_ERROR)

    def is_password_error_visible(self) -> bool:
        return self.is_visible(LoginLocators.PASSWORD_ERROR)

    def click_forgot_password(self):
        self.click(LoginLocators.FORGOT_PASSWORD)
