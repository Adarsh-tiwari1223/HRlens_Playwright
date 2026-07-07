import sys
import os
sys.path.append(os.getcwd())

from playwright.sync_api import sync_playwright
from core.config import settings

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(settings.BASE_URL)
    
    # Login
    from pages.login_page import LoginPage
    LoginPage(page).login(
        settings.USERS["admin"]["username"],
        settings.USERS["admin"]["password"]
    )
    page.wait_for_load_state("networkidle")
    
    # Go to settings
    page.goto(f"{settings.BASE_URL}/absence-settings")
    page.wait_for_load_state("networkidle")
    
    # Print options
    select_el = page.locator("select").first
    options = select_el.locator("option").all()
    print("=== DROPDOWN OPTIONS ===")
    for opt in options:
        val = opt.get_attribute("value")
        text = opt.inner_text().strip()
        print(f"Text: '{text}', Value: '{val}'")
        
    browser.close()
