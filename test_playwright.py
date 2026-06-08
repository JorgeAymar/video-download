
from playwright.sync_api import sync_playwright
import sys

url = "https://ninjasuite.app.clientclub.net/courses/products/6e514b35-eda8-40d2-a9b5-ea7925a2062e/categories/1712c6fc-c13c-4ba2-acd2-36a835b5a0d3/posts/4705813e-3316-4320-89cb-25999905cb57?source=courses"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle")
            print(f"Page Title: {page.title()}")
            
            # Check for video elements
            videos = page.locator("video").count()
            ifames = page.locator("iframe").count()
            print(f"Found {videos} video elements.")
            print(f"Found {ifames} iframe elements.")
            
            # Check for login indicators
            if "login" in page.url or "sign-in" in page.url or page.get_by_text("Login").count() > 0 or page.get_by_text("Sign In").count() > 0:
                print("Detected Login Page")
                
            page.screenshot(path="page_preview.png")
            print("Screenshot saved to page_preview.png")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
