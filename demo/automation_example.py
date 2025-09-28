#!/usr/bin/env python3
"""
Automation script to get reCAPTCHA token and test the API.
"""

import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_recaptcha_token(site_key, action="submit"):
    """Get reCAPTCHA token using Selenium automation."""

    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Create HTML with reCAPTCHA
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://www.google.com/recaptcha/enterprise.js?render={site_key}"></script>
        </head>
        <body>
            <div id="recaptcha-container"></div>
            <div id="token-display"></div>
            <script>
                grecaptcha.enterprise.ready(function() {{
                    grecaptcha.enterprise.execute('{site_key}', {{
                        action: '{action}'
                    }}).then(function(token) {{
                        document.getElementById('token-display').innerText = token;
                        console.log('Token generated:', token);
                    }});
                }});
            </script>
        </body>
        </html>
        """

        # Load the HTML
        driver.get(f"data:text/html;charset=utf-8,{html}")

        # Wait for token to be generated (up to 10 seconds)
        wait = WebDriverWait(driver, 10)
        wait.until(
            lambda driver: driver.find_element(By.ID, "token-display").text.strip()
            != ""
        )

        # Get the token
        token_element = driver.find_element(By.ID, "token-display")
        token = token_element.text.strip()

        print(f"✅ reCAPTCHA token generated: {token[:20]}...")
        return token

    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None
    finally:
        driver.quit()


def test_api_with_token(token, api_url="http://127.0.0.1:8001/api/contact/"):
    """Test the API with the generated token."""

    data = {
        "name": "Automated Test User",
        "email": "automation@example.com",
        "message": "This is an automated test message using real reCAPTCHA token!",
        "recaptcha_token": token,
    }

    try:
        response = requests.post(api_url, json=data, timeout=30)

        if response.status_code == 201:
            result = response.json()
            print("✅ API call successful!")
            print(f"   Contact ID: {result.get('contact_id')}")
            print(f"   reCAPTCHA Score: {result.get('recaptcha_score')}")
            print(f"   reCAPTCHA Action: {result.get('recaptcha_action')}")
            return True
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error calling API: {e}")
        return False


def main():
    """Main automation function."""

    # Your reCAPTCHA site key
    site_key = os.environ.get("RECAPTCHA_ENTERPRISE_SITE_KEY")
    if not site_key:
        print("❌ RECAPTCHA_ENTERPRISE_SITE_KEY is not set. Exiting.")
        return

    print("🤖 Starting reCAPTCHA automation...")
    print(f"   Site Key: {site_key}")

    # Step 1: Get reCAPTCHA token
    print("\n📝 Step 1: Generating reCAPTCHA token...")
    token = get_recaptcha_token(site_key)

    if not token:
        print("❌ Failed to generate token. Exiting.")
        return

    # Step 2: Test API with token
    print("\n🚀 Step 2: Testing API with token...")
    success = test_api_with_token(token)

    if success:
        print("\n🎉 Automation completed successfully!")
    else:
        print("\n💥 Automation failed!")


if __name__ == "__main__":
    main()
