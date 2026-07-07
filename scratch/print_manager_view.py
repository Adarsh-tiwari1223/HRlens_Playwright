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
    
    # Login as Vivek
    from pages.login_page import LoginPage
    LoginPage(page).login(
        settings.USERS["vivek"]["username"],
        settings.USERS["vivek"]["password"]
    )
    page.wait_for_load_state("networkidle")
    
    # Go to Absence Management
    page.goto(f"{settings.BASE_URL}/absence-management")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    
    # Print input info
    inputs = page.locator("input").all()
    print("=== INPUTS ON PAGE ===")
    for inp in inputs:
        placeholder = inp.get_attribute("placeholder")
        val = inp.input_value()
        print(f"Input placeholder: '{placeholder}', value: '{val}'")
        
    # Print rows
    rows = page.locator("tbody tr").all()
    print("=== ROWS ON PAGE ===")
    for r in rows:
        print(f"Row: '{r.inner_text().strip()}'")
        
    # Try searching "Radha Chaudhary"
    search_field = page.locator("input[placeholder*='Search']").first
    search_field.click()
    search_field.fill("")
    search_field.press_sequentially("Radha Chaudhary", delay=100)
    page.wait_for_timeout(2000)
    
    print("=== ROWS AFTER SEARCH ===")
    rows = page.locator("tbody tr").all()
    for r in rows:
        print(f"Row: '{r.inner_text().strip()}'")
        
    browser.close()
