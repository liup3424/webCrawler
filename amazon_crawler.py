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
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login_to_amazon(self, email: str, password: str) -> bool:
        """Login to Amazon and maintain session."""
        try:
            if not self.driver:
                self.setup_driver()
                
            # Navigate to Amazon login page
            self.driver.get("https://www.amazon.com/ap/signin")
            time.sleep(2)
            
            # Find and fill email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ap_email"))
            )
            email_input.send_keys(email)
            
            # Click continue
            continue_btn = self.driver.find_element(By.ID, "continue")
            continue_btn.click()
            time.sleep(2)
            
            # Find and fill password
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ap_password"))
            )
            password_input.send_keys(password)
            
            # Click sign in
            signin_btn = self.driver.find_element(By.ID, "signInSubmit")
            signin_btn.click()
            time.sleep(3)
            
            # Check if login was successful
            if "ap/signin" not in self.driver.current_url:
                print("Successfully logged in to Amazon!")
                return True
            else:
                print("Login failed!")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
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
            
    def search_products(self, keyword: str) -> List[Dict]:
        """Search for products on Amazon and return top 3 product details."""
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
            
            for i, element in enumerate(product_elements[:3]):  # Top 3 products
                try:
                    # Extract product information
                    title_element = element.find_element(By.CSS_SELECTOR, 'h2 a span')
                    title = title_element.text
                    
                    link_element = element.find_element(By.CSS_SELECTOR, 'h2 a')
                    product_url = link_element.get_attribute('href')
                    
                    # Try to get price
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, '.a-price-whole')
                        price = price_element.text
                    except:
                        price = "N/A"
                    
                    # Try to get rating
                    try:
                        rating_element = element.find_element(By.CSS_SELECTOR, '.a-icon-alt')
                        rating = rating_element.get_attribute('textContent')
                    except:
                        rating = "N/A"
                    
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
                
            # Navigate to product reviews page
            reviews_url = product_url.replace('/dp/', '/product-reviews/') + '/ref=cm_cr_dp_d_show_all_btm'
            self.driver.get(reviews_url)
            time.sleep(3)
            
            # Apply star filter if specified
            if star_filter:
                try:
                    star_filter_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-hook="review-star-filter-{star_filter}"]')
                    star_filter_btn.click()
                    time.sleep(2)
                except:
                    print(f"Could not apply {star_filter}-star filter")
            
            reviews = []
            page_count = 0
            
            while page_count < max_pages:
                # Find review elements
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-hook="review"]')
                
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
                        next_btn = self.driver.find_element(By.CSS_SELECTOR, '.a-pagination .a-last a')
                        if next_btn.is_enabled():
                            next_btn.click()
                            time.sleep(3)
                        else:
                            break
                    except:
                        print("No more pages available")
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
