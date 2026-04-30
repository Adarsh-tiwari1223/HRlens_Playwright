from pages.base_page import BasePage


class LoginPage(BasePage):
 # ----------------------Locators---------------------------------------
    EMAIL_INPUT = "#email"
    PWD_INPUT = "#password"
    LOGIN_BTN = ".login-button"
    FORGOT_PWD_LINK = "text=Forgot Password?"
    SEND_OTP_BTN = "button:has-text('Send OTP')"
#----------------------Error messages---------------------------------------
    EMAIL_REQUIRED = "text=Email is required"
    PWD_REQUIRED = "text=Password is required"
    INVALID_CREDS = "text=Email or password is incorrect"
    OTP_EMAIL_REQUIRED = "text=Please enter your email"
 
 #---------------------------------Actions------------------------------------
    def login(self, email: str, pwd: str):
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PWD_INPUT, pwd)
        self.click(self.LOGIN_BTN)

    def click_login(self):
        self.click(self.LOGIN_BTN)

    def click_forgot_password(self):
        self.click(self.FORGOT_PWD_LINK)

    def click_send_otp(self):
        self.click(self.SEND_OTP_BTN)
