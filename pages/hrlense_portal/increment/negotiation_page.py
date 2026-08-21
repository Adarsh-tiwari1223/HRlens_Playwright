from pages.base_page import BasePage


class NegotiationPage(BasePage):
    # Locators
    NEGOTIATION_TAB = "text=Negotiation"
    ACCEPT_BTN = "button:has-text('Accept')"
    REJECT_BTN = "button:has-text('Reject')"
    COUNTER_OFFER_INPUT = "[data-testid='counter-offer']"
    SUBMIT_BTN = "button:has-text('Submit')"
    SUCCESS_TOAST = "text=Negotiation Submitted"

    def navigate_to_negotiation(self):
        self.page.locator(self.NEGOTIATION_TAB).click()

    def accept_offer(self):
        self.page.locator(self.ACCEPT_BTN).click()

    def reject_offer(self):
        self.page.locator(self.REJECT_BTN).click()

    def enter_counter_offer(self, amount: str):
        self.page.locator(self.COUNTER_OFFER_INPUT).fill(amount)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def is_success_visible(self) -> bool:
        return self.page.locator(self.SUCCESS_TOAST).is_visible()
