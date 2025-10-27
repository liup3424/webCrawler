import os
import json
import csv
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AmazonCrawler:
    def __init__(self, headless: bool = True):
        """Initialize the Amazon crawler with Selenium WebDriver."""
        self.session = requests.Session()
        self.ua = UserAgent()
        self.headless = headless
        self.driver = None
        self.setup_session()
        
    def setup_session(self):
        """Setup requests session with headers."""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def setup_driver(self):
        """Setup Chrome WebDriver with options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
    def manual_login_and_save_cookies(self, cookie_file: str = "amazon_cookies.json") -> bool:
        """Allow manual login and save cookies for future use."""
        try:
            if not self.driver:
                self.setup_driver()
            
            print("=" * 60)
            print("MANUAL LOGIN MODE")
            print("=" * 60)
            print("1. A browser window will open")
            print("2. Please log in to Amazon manually")
            print("3. You have 60 seconds to complete login")
            print("4. Cookies will be saved automatically")
            print("=" * 60)
            
            # Use the exact login URL from your example
            login_url = ("https://www.amazon.com/ap/signin"
                        "?openid.return_to=https%3A%2F%2Fwww.amazon.com%2F"
                        "&openid.pape.max_auth_age=0"
                        "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
                        "&openid.assoc_handle=usflex"
                        "&openid.mode=checkid_setup"
                        "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
                        "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
            
            self.driver.get(login_url)
            
            print("Please log in manually — you have 60 seconds...")
            time.sleep(60)
            
            # Extract cookies
            cookies = self.driver.get_cookies()
            
            # Save cookies
            import json
            with open(cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)
            
            print(f"✅ Cookies saved to {cookie_file}")
            print("You can now use --load-cookies to reuse this session")
            
            return True
                
        except Exception as e:
            print(f"Error during manual login: {e}")
            return False
    
    def load_cookies(self, cookie_file: str = "amazon_cookies.json") -> bool:
        """Load saved cookies to restore login session."""
        try:
            if not self.driver:
                self.setup_driver()
            
            import json
            import os
            
            if not os.path.exists(cookie_file):
                return False
            
            print(f"Loading cookies from {cookie_file}...")
            
            # Load cookies from file
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # Navigate to Amazon first
            self.driver.get("https://www.amazon.com")
            time.sleep(3)
            
            # Add cookies to the driver
            cookies_added = 0
            for cookie in cookies:
                try:
                    # Remove problematic keys
                    cookie_copy = cookie.copy()
                    if 'expiry' in cookie_copy and cookie_copy['expiry'] is None:
                        del cookie_copy['expiry']
                    if 'expires' in cookie_copy and cookie_copy['expires'] is None:
                        del cookie_copy['expires']
                    
                    self.driver.add_cookie(cookie_copy)
                    cookies_added += 1
                except Exception as e:
                    print(f"Warning: Could not add cookie {cookie.get('name', 'unknown')}: {e}")
            
            print(f"Added {cookies_added} cookies")
            
            # Navigate to a specific page to test cookies
            self.driver.get("https://www.amazon.com/gp/css/homepage.html")
            time.sleep(3)
            
            # Check if we're logged in by looking for account indicators
            page_source = self.driver.page_source.lower()
            if "hello," in page_source or "your account" in page_source:
                print("✅ Cookies working - logged in detected")
            else:
                print("⚠️ Cookies may not be working properly")
            
            # Check if login was successful by looking for account indicators
            page_source = self.driver.page_source.lower()
            success_indicators = [
                "hello," in page_source,
                "your account" in page_source,
                "sign out" in page_source,
                "account & lists" in page_source
            ]
            
            if any(success_indicators):
                print("✅ Successfully loaded saved cookies!")
                return True
            else:
                print("❌ Cookies may be expired or invalid. Please login manually again.")
                return False
                
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
        """Login to Amazon and maintain session."""
        try:
            if not self.driver:
                self.setup_driver()
                
            print("Navigating to Amazon login page...")
            # Navigate to Amazon login page
            self.driver.get("https://www.amazon.com/ap/signin")
            time.sleep(3)
            
            # Check if we're on the right page
            print(f"Current URL: {self.driver.current_url}")
            
            # Try multiple selectors for email input
            email_input = None
            email_selectors = [
                (By.ID, "ap_email"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name='email']")
            ]
            
            for selector_type, selector_value in email_selectors:
                try:
                    email_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"Found email input with selector: {selector_type}={selector_value}")
                    break
                except:
                    continue
            
            if not email_input:
                print("Could not find email input field")
                return False
            
            # Clear and fill email
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)
            
            # Try multiple selectors for continue button
            continue_btn = None
            continue_selectors = [
                (By.ID, "continue"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, ".a-button-primary input")
            ]
            
            for selector_type, selector_value in continue_selectors:
                try:
                    continue_btn = self.driver.find_element(selector_type, selector_value)
                    print(f"Found continue button with selector: {selector_type}={selector_value}")
                    break
                except:
                    continue
            
            if not continue_btn:
                print("Could not find continue button")
                return False
            
            continue_btn.click()
            time.sleep(3)
            
            # Try multiple selectors for password input
            password_input = None
            password_selectors = [
                (By.ID, "ap_password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name='password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"Found password input with selector: {selector_type}={selector_value}")
                    break
                except:
                    continue
            
            if not password_input:
                print("Could not find password input field")
                return False
            
            # Clear and fill password
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
            
            # Try multiple selectors for sign in button
            signin_btn = None
            signin_selectors = [
                (By.ID, "signInSubmit"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, ".a-button-primary input")
            ]
            
            for selector_type, selector_value in signin_selectors:
                try:
                    signin_btn = self.driver.find_element(selector_type, selector_value)
                    print(f"Found sign in button with selector: {selector_type}={selector_value}")
                    break
                except:
                    continue
            
            if not signin_btn:
                print("Could not find sign in button")
                return False
            
            signin_btn.click()
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            print(f"After login, current URL: {current_url}")
            
            # Check for various success indicators
            success_indicators = [
                "ap/signin" not in current_url,
                "your-account" in current_url,
                "nav-account" in current_url,
                "sign-out" in current_url
            ]
            
            if any(success_indicators):
                print("Successfully logged in to Amazon!")
                return True
            else:
                print("Login failed - still on login page or redirected to error page")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            print(f"Error type: {type(e).__name__}")
            return False
            
    def get_cookies(self) -> Dict:
        """Get cookies from the current session."""
        if self.driver:
            return {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
        return {}
        
    def update_session_cookies(self):
        """Update requests session with cookies from WebDriver."""
        cookies = self.get_cookies()
        for name, value in cookies.items():
            self.session.cookies.set(name, value)
            
    def search_products(self, keyword: str, top_count: int = 3) -> List[Dict]:
        """Search for products on Amazon and return top N product details."""
        try:
            if not self.driver:
                self.setup_driver()
                
            # Navigate to Amazon search
            search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Update session cookies
            self.update_session_cookies()
            
            # Find product containers
            products = []
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
            print(f"Found {len(product_elements)} product elements")
            
            # If no elements found with the main selector, try alternative selectors
            if not product_elements:
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, '.s-result-item')
                print(f"Found {len(product_elements)} product elements with alternative selector")
            
            if not product_elements:
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-asin]')
                print(f"Found {len(product_elements)} product elements with ASIN selector")
            
            for i, element in enumerate(product_elements[:top_count]):  # Top N products
                try:
                    # Extract product information - try multiple selectors for title
                    title = "N/A"
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, 'h2 a span')
                        title = title_element.text
                    except:
                        try:
                            title_element = element.find_element(By.CSS_SELECTOR, 'h2 a')
                            title = title_element.text
                        except:
                            try:
                                title_element = element.find_element(By.CSS_SELECTOR, '.s-size-mini .s-color-base')
                                title = title_element.text
                            except:
                                try:
                                    title_element = element.find_element(By.CSS_SELECTOR, 'h2 span')
                                    title = title_element.text
                                except:
                                    try:
                                        title_element = element.find_element(By.CSS_SELECTOR, '.s-color-base')
                                        title = title_element.text
                                    except:
                                        try:
                                            title_element = element.find_element(By.CSS_SELECTOR, 'a[href*="/dp/"] span')
                                            title = title_element.text
                                        except:
                                            pass
                    
                    # Get product URL - try multiple selectors with debugging
                    product_url = "N/A"
                    url_selectors = [
                        'h2 a',
                        'a[href*="/dp/"]',
                        'a[href*="/gp/product/"]',
                        '.s-size-mini a',
                        'a[data-hook="product-link"]',
                        'a[href*="amazon.com"]',
                        'a[href*="/product/"]',
                        '.s-link-style a',
                        'a[href*="amazon.com/dp/"]',
                        'a[href*="amazon.com/gp/product/"]'
                    ]
                    
                    print(f"  Debugging URL extraction for product {i+1}...")
                    for j, selector in enumerate(url_selectors):
                        try:
                            link_elements = element.find_elements(By.CSS_SELECTOR, selector)
                            if link_elements:
                                for link_element in link_elements:
                                    href = link_element.get_attribute('href')
                                    if href and ('/dp/' in href or '/gp/product/' in href or '/product/' in href):
                                        product_url = href
                                        print(f"    ✅ Found URL with selector {j+1}: {selector}")
                                        break
                                if product_url != "N/A":
                                    break
                        except Exception as e:
                            print(f"    ❌ Selector {j+1} failed: {e}")
                            continue
                    
                    if product_url == "N/A":
                        print(f"    ⚠️ No direct URL found, checking for sponsored links...")
                        # Try to find any link in the element and decode sponsored URLs
                        try:
                            all_links = element.find_elements(By.TAG_NAME, 'a')
                            print(f"    Found {len(all_links)} total links in element")
                            for link in all_links:
                                href = link.get_attribute('href')
                                if href and 'sspa/click' in href and 'url=' in href:
                                    # This is a sponsored link, extract the real URL
                                    import urllib.parse
                                    try:
                                        # Extract the url parameter
                                        parsed_url = urllib.parse.urlparse(href)
                                        query_params = urllib.parse.parse_qs(parsed_url.query)
                                        if 'url' in query_params:
                                            encoded_url = query_params['url'][0]
                                            decoded_url = urllib.parse.unquote(encoded_url)
                                            if decoded_url.startswith('/'):
                                                decoded_url = 'https://www.amazon.com' + decoded_url
                                            if '/dp/' in decoded_url or '/gp/product/' in decoded_url:
                                                product_url = decoded_url
                                                print(f"    ✅ Extracted URL from sponsored link: {decoded_url}")
                                                break
                                    except Exception as e:
                                        print(f"    ❌ Failed to decode sponsored URL: {e}")
                                        continue
                                elif href and ('/dp/' in href or '/gp/product/' in href):
                                    product_url = href
                                    print(f"    ✅ Found direct URL: {href}")
                                    break
                        except Exception as e:
                            print(f"    ❌ Error processing links: {e}")
                            pass
                    
                    # Try to get price
                    price = "N/A"
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, '.a-price-whole')
                        price = price_element.text
                    except:
                        try:
                            price_element = element.find_element(By.CSS_SELECTOR, '.a-price .a-offscreen')
                            price = price_element.text
                        except:
                            pass
                    
                    # Try to get rating
                    rating = "N/A"
                    try:
                        rating_element = element.find_element(By.CSS_SELECTOR, '.a-icon-alt')
                        rating = rating_element.get_attribute('textContent')
                    except:
                        try:
                            rating_element = element.find_element(By.CSS_SELECTOR, '[data-hook="rating-out-of-text"]')
                            rating = rating_element.text
                        except:
                            pass
                    
                    products.append({
                        'rank': i + 1,
                        'title': title,
                        'url': product_url,
                        'price': price,
                        'rating': rating
                    })
                    
                except Exception as e:
                    print(f"Error extracting product {i+1}: {e}")
                    continue
                    
            return products
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
            
    def scrape_reviews(self, product_url: str, star_filter: Optional[int] = None, max_pages: int = 2) -> List[Dict]:
        """Scrape reviews for a specific product with optional star filtering."""
        try:
            if not self.driver:
                self.setup_driver()
            
            # Check if we're still logged in before attempting to scrape
            self.driver.get("https://www.amazon.com")
            time.sleep(2)
            page_source = self.driver.page_source.lower()
            if "sign in" in page_source and "hello," not in page_source:
                print("⚠️ Session expired - cookies may need to be refreshed")
                return []
                
            # Navigate to product reviews page
            if '/dp/' in product_url:
                # Extract ASIN from URL
                asin = product_url.split('/dp/')[1].split('/')[0]
                reviews_url = f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm"
            else:
                print(f"Invalid product URL format: {product_url}")
                return []
            
            print(f"Navigating to reviews URL: {reviews_url}")
            
            # Add random delay to appear more human-like
            import random
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # Try different review page URLs
            review_urls = [
                reviews_url,
                f"https://www.amazon.com/product-reviews/{asin}/",
                f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
                f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent"
            ]
            
            success = False
            for url in review_urls:
                try:
                    print(f"Trying URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    current_url = self.driver.current_url
                    print(f"Current URL after navigation: {current_url}")
                    
                    # Check if we're on a valid reviews page
                    if "product-reviews" in current_url and "signin" not in current_url:
                        print("✅ Successfully reached reviews page")
                        success = True
                        break
                    elif "signin" in current_url:
                        print("❌ Redirected to login page")
                        continue
                    else:
                        print("⚠️ Unexpected page, trying next URL")
                        continue
                        
                except Exception as e:
                    print(f"Error with URL {url}: {e}")
                    continue
            
            if not success:
                print("❌ Could not access any review page")
                return []
            
            # Apply star filter if specified
            if star_filter:
                try:
                    star_filter_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-hook="review-star-filter-{star_filter}"]')
                    star_filter_btn.click()
                    time.sleep(3)
                    print(f"Applied {star_filter}-star filter")
                except:
                    print(f"Could not apply {star_filter}-star filter")
            
            reviews = []
            page_count = 0
            
            while page_count < max_pages:
                print(f"Scraping page {page_count + 1}...")
                
                # Try multiple selectors for review elements
                review_elements = []
                review_selectors = [
                    '[data-hook="review"]',
                    '.review',
                    '[data-hook="review-body"]',
                    '.a-section.review',
                    '.cr-original-review-item'
                ]
                
                for selector in review_selectors:
                    review_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if review_elements:
                        print(f"Found {len(review_elements)} reviews with selector: {selector}")
                        break
                
                if not review_elements:
                    print("❌ No review elements found on this page")
                    break
                
                for element in review_elements:
                    try:
                        # Extract review data
                        review_data = {}
                        
                        # Review text
                        try:
                            review_text_element = element.find_element(By.CSS_SELECTOR, '[data-hook="review-body"] span')
                            review_data['review_text'] = review_text_element.text.strip()
                        except:
                            review_data['review_text'] = "N/A"
                        
                        # Star rating
                        try:
                            rating_element = element.find_element(By.CSS_SELECTOR, '[data-hook="review-star-rating"]')
                            rating_text = rating_element.get_attribute('textContent')
                            review_data['star_rating'] = rating_text.split()[0]
                        except:
                            review_data['star_rating'] = "N/A"
                        
                        # Review date
                        try:
                            date_element = element.find_element(By.CSS_SELECTOR, '[data-hook="review-date"]')
                            review_data['review_date'] = date_element.text.strip()
                        except:
                            review_data['review_date'] = "N/A"
                        
                        # Reviewer nickname
                        try:
                            reviewer_element = element.find_element(By.CSS_SELECTOR, '[data-hook="review-author"]')
                            review_data['reviewer_nickname'] = reviewer_element.text.strip()
                        except:
                            review_data['reviewer_nickname'] = "N/A"
                        
                        # Review title
                        try:
                            title_element = element.find_element(By.CSS_SELECTOR, '[data-hook="review-title"] span')
                            review_data['review_title'] = title_element.text.strip()
                        except:
                            review_data['review_title'] = "N/A"
                        
                        reviews.append(review_data)
                        
                    except Exception as e:
                        print(f"Error extracting review: {e}")
                        continue
                
                # Try to go to next page
                page_count += 1
                if page_count < max_pages:
                    try:
                        # Try multiple selectors for next page button
                        next_btn = None
                        next_selectors = [
                            '.a-pagination .a-last a',
                            '.a-pagination .a-next',
                            '[aria-label="Next Page"]',
                            '.a-pagination .a-last',
                            'a[aria-label="Next Page"]'
                        ]
                        
                        for selector in next_selectors:
                            try:
                                next_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if next_btn.is_enabled():
                                    print(f"Found next page button with selector: {selector}")
                                    break
                            except:
                                continue
                        
                        if next_btn and next_btn.is_enabled():
                            next_btn.click()
                            time.sleep(3)
                            print(f"Navigated to page {page_count + 1}")
                        else:
                            print("No more pages available")
                            break
                    except Exception as e:
                        print(f"No more pages available: {e}")
                        break
                        
            return reviews
            
        except Exception as e:
            print(f"Review scraping error: {e}")
            return []
            
    def save_to_json(self, data: List[Dict], filename: str):
        """Save data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def save_to_csv(self, data: List[Dict], filename: str):
        """Save data to CSV file."""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8')
            
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
