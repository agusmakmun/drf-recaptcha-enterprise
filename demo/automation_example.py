#!/usr/bin/env python3
"""
Automation script to get reCAPTCHA token and test the API.
"""

import os
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


# List of 10 different user agents for randomization
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
]


def get_random_headers():
    """Get random headers including user agent."""
    user_agent = random.choice(USER_AGENTS)
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def get_recaptcha_token(site_key, action="submit"):
    """Get reCAPTCHA token using Selenium automation."""

    # Setup Chrome driver with random user agent
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Add random user agent
    random_headers = get_random_headers()
    chrome_options.add_argument(f"--user-agent={random_headers['User-Agent']}")

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
        print(f"   Using User-Agent: {random_headers['User-Agent'][:50]}...")
        return token, random_headers

    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None, None
    finally:
        driver.quit()


def test_api_with_token(token, headers, api_url="http://127.0.0.1:8000/api/contact/"):
    """Test the API with the generated token using the same headers."""

    data = {
        "name": "Automated Test User",
        "email": "automation@example.com",
        "message": "This is an automated test message using real reCAPTCHA token!",
        "recaptcha_token": token,
    }

    # Use the same headers from the token generation
    api_headers = headers.copy()
    api_headers.update(
        {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    try:
        response = requests.post(api_url, json=data, headers=api_headers, timeout=30)

        if response.status_code == 201:
            result = response.json()
            print("✅ API call successful!")
            print(f"   Contact ID: {result.get('contact_id')}")
            print(f"   reCAPTCHA Score: {result.get('recaptcha_score')}")
            print(f"   reCAPTCHA Action: {result.get('recaptcha_action')}")
            print(f"   Using User-Agent: {api_headers['User-Agent'][:50]}...")
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
    token, headers = get_recaptcha_token(site_key)

    if not token or not headers:
        print("❌ Failed to generate token. Exiting.")
        return

    # Step 2: Test API with token using the same headers
    print("\n🚀 Step 2: Testing API with token...")
    success = test_api_with_token(token, headers)

    if success:
        print("\n🎉 Automation completed successfully!")
    else:
        print("\n💥 Automation failed!")


if __name__ == "__main__":
    main()
