"""
Authentication and cookie management for Amazon Web Crawler.
"""

import os
import json
import time
from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .config import COOKIE_FILE, MANUAL_LOGIN_TIMEOUT, AMAZON_LOGIN_URL, LOGIN_INDICATORS


class AuthManager:
    """Handles authentication and cookie management for Amazon."""
    
    def __init__(self, driver):
        """Initialize the authentication manager with a WebDriver instance."""
        self.driver = driver
    
    def manual_login_and_save_cookies(self) -> bool:
        """
        Perform manual login and save cookies for future use.
        
        Returns:
            bool: True if login was successful, False otherwise.
        """
        try:
            print("🌐 Opening Amazon login page...")
            self.driver.get(AMAZON_LOGIN_URL)
            
            print("⏳ Please log in manually in the browser window...")
            print(f"⏰ You have {MANUAL_LOGIN_TIMEOUT} seconds to complete the login.")
            
            # Wait for manual login
            time.sleep(MANUAL_LOGIN_TIMEOUT)
            
            # Check if login was successful
            if self._is_logged_in():
                print("✅ Login successful! Saving cookies...")
                self._save_cookies()
                return True
            else:
                print("❌ Login failed or timeout reached.")
                return False
                
        except Exception as e:
            print(f"❌ Manual login error: {e}")
            return False
    
    def load_cookies(self) -> bool:
        """
        Load cookies from file and apply them to the current session.
        
        Returns:
            bool: True if cookies were loaded successfully, False otherwise.
        """
        try:
            if not os.path.exists(COOKIE_FILE):
                print(f"❌ Cookie file not found: {COOKIE_FILE}")
                return False
            
            print(f"📂 Loading cookies from {COOKIE_FILE}...")
            
            # Load cookies from file
            with open(COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
            
            # Navigate to Amazon first
            self.driver.get("https://www.amazon.com")
            time.sleep(2)
            
            # Add cookies to the session
            for cookie in cookies:
                try:
                    # Remove problematic keys
                    cookie_dict = cookie.copy()
                    if 'expiry' in cookie_dict and cookie_dict['expiry'] is None:
                        del cookie_dict['expiry']
                    if 'expires' in cookie_dict and cookie_dict['expires'] is None:
                        del cookie_dict['expires']
                    
                    self.driver.add_cookie(cookie_dict)
                except WebDriverException as e:
                    print(f"⚠️ Warning: Could not add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue
            
            # Refresh the page to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Verify login status
            if self._is_logged_in():
                print("✅ Cookies loaded successfully!")
                return True
            else:
                print("❌ Cookies appear to be expired or invalid.")
                return False
                
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return False
    
    def _save_cookies(self) -> None:
        """Save current session cookies to file."""
        try:
            cookies = self.driver.get_cookies()
            with open(COOKIE_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"💾 Cookies saved to {COOKIE_FILE}")
        except Exception as e:
            print(f"❌ Error saving cookies: {e}")
    
    def _is_logged_in(self) -> bool:
        """
        Check if the user is currently logged in to Amazon.
        
        Returns:
            bool: True if logged in, False otherwise.
        """
        try:
            # Get page source and check for login indicators
            page_source = self.driver.page_source.lower()
            
            # Check for login indicators
            is_logged_in = any(indicator in page_source for indicator in LOGIN_INDICATORS)
            
            # Also check if we're NOT on a sign-in page
            current_url = self.driver.current_url.lower()
            not_on_signin = "signin" not in current_url and "ap/signin" not in current_url
            
            return is_logged_in and not_on_signin
            
        except Exception as e:
            print(f"⚠️ Error checking login status: {e}")
            return False
    
    def check_session_status(self) -> bool:
        """
        Check if the current session is still valid.
        
        Returns:
            bool: True if session is valid, False if expired.
        """
        try:
            self.driver.get("https://www.amazon.com")
            time.sleep(2)
            return self._is_logged_in()
        except Exception as e:
            print(f"⚠️ Error checking session status: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """
        Attempt to refresh the session by reloading cookies.
        
        Returns:
            bool: True if session was refreshed successfully, False otherwise.
        """
        print("🔄 Attempting to refresh session...")
        return self.load_cookies()
