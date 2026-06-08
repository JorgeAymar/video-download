
from playwright.sync_api import sync_playwright
import time
import sys
import os

# Target URL (pass as first CLI arg, or set TARGET_URL env var)
if len(sys.argv) > 1:
    TARGET_URL = sys.argv[1]
else:
    TARGET_URL = os.environ.get("TARGET_URL", "")
    if not TARGET_URL:
        print("ERROR: Provide a target URL as an argument or set TARGET_URL env var.")
        sys.exit(1)

# Credentials - read from environment (never hardcode secrets)
EMAIL = os.environ.get("NINJASUITE_EMAIL", "")
PASSWORD = os.environ.get("NINJASUITE_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("ERROR: Set NINJASUITE_EMAIL and NINJASUITE_PASSWORD environment variables.")
    print("Tip: copy .env.example to .env and fill in your credentials.")
    sys.exit(1)

def run():
    print("Starting Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False if you want to see the browser
        context = browser.new_context()
        page = context.new_page()

        # Variable to store found video URL
        found_url = None

        # Network listener
        def handle_request(route):
            nonlocal found_url
            url = route.request.url
            if ("iframe.mediadelivery.net" in url or ".m3u8" in url or ".mp4" in url) and "favicon" not in url:
                print(f"[FOUND] Potential Video URL: {url}")
                found_url = url
            route.continue_()

        # Subscribe to network events (better than route if we just want to listen)
        # But logging request is enough
        page.on("request", lambda request: check_url(request.url))

        def check_url(url):
            nonlocal found_url
            if found_url: return
            if "iframe.mediadelivery.net" in url:
                print(f"!!! FOUND IFRAME URL: {url}")
                found_url = url
            elif ".m3u8" in url and "playlist" in url:
                 print(f"!!! FOUND M3U8 URL: {url}")
                 found_url = url

        try:
            print(f"Navigating to {TARGET_URL}...")
            page.goto(TARGET_URL)
            
            # Check if we are on login page
            # Usually redirects to a login page if not auth
            time.sleep(5)
            print(f"DEBUG: Current URL: {page.url}")
            
            # Check for email input in main page OR frames
            # We must find a VISIBLE input
            email_input = None
            
            # Use specific IDs found in HTML analysis
            # Email is type="text", id parent is "sign-in-form-email"
            print("Looking for #sign-in-form-email input...")
            email_input = page.locator("#sign-in-form-email input").first
            
            if email_input.count() > 0 and email_input.is_visible():
                print("Found email input by ID.")
            else:
                # Fallback to placeholder
                email_input = page.locator("input[placeholder='Correo electrónico']").first

            if email_input.count() > 0 and email_input.is_visible():
                print("detected Login Page via Input. Logging in...")
                
                # Fill Email
                email_input.fill(EMAIL)
                
                # Fill Password
                password_input = page.locator("#sign-in-form-password input").first
                if password_input.count() == 0:
                     password_input = page.locator("input[placeholder='Contraseña']").first
                
                # If we have password input, fill it
                if password_input.count() > 0:
                     password_input.fill(PASSWORD)
                
                # Click Login
                # Try generic selectors for button
                submit_btn = None
                # ID found in HTML: login--button
                submit_btn = page.locator("#login--button").first
                
                if submit_btn.count() > 0:
                     # Check if disabled
                     if "disabled" in submit_btn.get_attribute("class"):
                         print("WARNING: Login button is disabled!")
                     else:
                         print("Clicking login button...")
                         submit_btn.click()
                         # Also press enter just in case
                         # page.keyboard.press("Enter")
                else:
                     print("Submit button not found, pressing Enter on password...")
                     if password_input:
                        password_input.press("Enter")
                
                print("Login submitted. Waiting for navigation/redirect...")
                
                # Wait up to 15s for URL change
                try:
                    page.wait_for_url(lambda u: "login" not in u, timeout=15000)
                    print("Redirection Success!")
                except Exception as e:
                    print(f"Timeout waiting for URL change: {e}")
                
                # Check for error messages
                print(f"Post-Login URL: {page.url}")
                page_text = page.inner_text("body")
                with open("post_login.txt", "w") as f:
                    f.write(page_text)
                print("Dumped post-login text to post_login.txt")
                
                if "invalid" in page_text.lower() or "error" in page_text.lower() or "incorrect" in page_text.lower():
                     print("POSSIBLE LOGIN ERROR detected in page text.")
                
                # Force navigation to target if we are not on it
                if TARGET_URL not in page.url:
                    print(f"Redirecting from {page.url} to target URL...")
                    page.goto(TARGET_URL)
                    time.sleep(5)
                
                print("Waiting for video content to load...")
                
                # Check for error messages
                print(f"Post-Login URL: {page.url}")
                page.screenshot(path="post_login_state.png")
                page_text = page.inner_text("body")
                if "invalid" in page_text.lower() or "error" in page_text.lower() or "incorrect" in page_text.lower():
                     print("POSSIBLE LOGIN ERROR detected in page text.")
                     print("-" * 20)
                     print(page_text[:500]) # First 500 chars
                     print("-" * 20)
                
                # Wait for potential redirect
                time.sleep(5)
            
            else:
                print("No visible login inputs found. Assuming already logged in or different page structure.")
                print(f"Current URL: {page.url}")
                
                if "login" in page.url:
                    print("URL contains 'login' but no inputs found. Dumping HTML...")
                    with open("login_source.html", "w") as f:
                        f.write(page.content())
                    page.screenshot(path="login_debug.png")
                    
                    # Try finding ANY input to see what's there
                    print("Listing ALL inputs:")
                    for inp in page.locator("input").all():
                        if inp.is_visible():
                            print(f"Visible Input: {inp.get_attribute('outerHTML')}")
                
                # After login, it might go to dashboard. We should force go to target url again if needed
                if TARGET_URL not in page.url:
                    print("Redirecting to target URL...")
                    page.goto(TARGET_URL)
            
            print("Waiting for video content to load...")
            # specific wait for potential iframes
            time.sleep(7) 
            
            # If network listener collected something
            if found_url:
                print("-" * 30)
                print(f"FINAL VIDEO URL: {found_url}")
                print("-" * 30)
                # Create a file with the URL so we can read it easily or just parse stdout
                with open("extracted_url.txt", "w") as f:
                    f.write(found_url)
            else:
                print("No video URL found via network. Checking frames...")
                # Inspect frames
                for frame in page.frames:
                    print(f"Frame URL: {frame.url}")
                    if "iframe.mediadelivery.net" in frame.url:
                        print(f"!!! FOUND FRAME: {frame.url}")
                        with open("extracted_url.txt", "w") as f:
                            f.write(frame.url)
                        break
                        
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="error_state.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
