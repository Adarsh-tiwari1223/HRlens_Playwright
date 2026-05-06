import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url: str):
        logger.info(f"navigate → {url}")
        self.page.goto(url)

    def click(self, locator: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).click()
        logger.info(f"click → {locator}")

    def fill(self, locator: str, value: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).fill(value)
        logger.info(f"fill → {locator} = '{value}'")

    def get_text(self, locator: str) -> str:
        self.page.locator(locator).wait_for(state="visible")
        text = self.page.locator(locator).inner_text()
        logger.info(f"get_text → {locator} = '{text}'")
        return text

    def get_all_texts(self, locator: str) -> list[str]:
        texts = self.page.locator(locator).all_inner_texts()
        logger.info(f"get_all_texts → {locator} = {texts}")
        return texts

    def is_visible(self, locator: str) -> bool:
        result = self.page.locator(locator).is_visible()
        logger.info(f"is_visible → {locator} = {result}")
        return result

    def is_enabled(self, locator: str) -> bool:
        result = self.page.locator(locator).is_enabled()
        logger.info(f"is_enabled → {locator} = {result}")
        return result

    def select_option(self, locator: str, value: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).select_option(value)
        logger.info(f"select_option → {locator} = '{value}'")

    def wait_for_url(self, partial: str):
        self.page.wait_for_url(f"**{partial}**")
        logger.info(f"wait_for_url → '{partial}'")

    def wait_for_toast(self, locator: str) -> str:
        self.page.locator(locator).wait_for(state="visible")
        text = self.page.locator(locator).inner_text()
        logger.info(f"toast → '{text}'")
        return text

    def get_all_toasts(self, locator: str) -> list[str]:
        self.page.locator(locator).wait_for(state="visible")
        toasts = self.page.locator(f"{locator} [id*='toast'][id*='title']").all_inner_texts()
        logger.info(f"toasts → {toasts}")
        return toasts

    def wait_for_hidden(self, locator: str):
        self.page.locator(locator).wait_for(state="hidden")
        logger.info(f"wait_for_hidden → {locator}")

    def get_count(self, locator: str) -> int:
        count = self.page.locator(locator).count()
        logger.info(f"get_count → {locator} = {count}")
        return count

    def upload_file(self, locator: str, file_path: str):
        self.page.locator(locator).set_input_files(file_path)
        logger.info(f"upload_file → {locator} = '{file_path}'")

    def scroll_into_view(self, locator: str):
        self.page.locator(locator).scroll_into_view_if_needed()
        logger.info(f"scroll_into_view → {locator}")

    def reload(self):
        self.page.reload()
        logger.info("reload")

