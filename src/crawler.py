"""
Main Amazon Web Crawler class with modular architecture.
"""

import os
import time
import random
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
from dotenv import load_dotenv

from .config import AMAZON_BASE_URL, CHROME_OPTIONS, SELECTORS, DEFAULT_SETTINGS
from .auth import AuthManager
from .utils import DataExtractor
from .data import DataProcessor

# Load environment variables
load_dotenv()


class AmazonCrawler:
    """Main Amazon Web Crawler with modular architecture."""
    
    def __init__(self, headless: bool = True, output_dir: str = None):
        """
        Initialize the Amazon crawler.
        
        Args:
            headless: Whether to run browser in headless mode
            output_dir: Directory for output files
        """
        self.session = requests.Session()
        self.ua = UserAgent()
        self.headless = headless
        self.driver = None
        self.output_dir = output_dir or DEFAULT_SETTINGS['output_dir']
        
        # Initialize modules
        self.auth_manager = None
        self.data_extractor = None
        self.data_processor = DataProcessor(self.output_dir)
        
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
        
        # Add all Chrome options from config
        for option in CHROME_OPTIONS:
            chrome_options.add_argument(option)
        
        # Additional anti-detection measures
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to hide automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Initialize modules that depend on driver
            self.auth_manager = AuthManager(self.driver)
            self.data_extractor = DataExtractor(self.driver)
            
            print("✅ WebDriver initialized successfully")
            
        except Exception as e:
            print(f"❌ Error setting up WebDriver: {e}")
            raise
    
    def search_products(self, keyword: str, top_count: int = 3) -> List[Dict]:
        """
        Search for products on Amazon by keyword.
        
        Args:
            keyword: Search keyword
            top_count: Number of top products to return
            
        Returns:
            List of product dictionaries
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            print(f"🔍 Searching for: '{keyword}'")
            
            # Construct search URL
            search_url = f"{AMAZON_BASE_URL}/s?k={keyword.replace(' ', '+')}"
            print(f"🌐 Navigating to: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(3)
            
            # Find product elements
            product_elements = self.data_extractor.find_elements_by_selectors(
                SELECTORS['product_elements']
            )
            
            if not product_elements:
                print("❌ No products found")
                return []
            
            print(f"📦 Found {len(product_elements)} products")
            
            # Extract product data
            products = []
            for i, element in enumerate(product_elements[:top_count]):
                print(f"📝 Processing product {i+1}/{top_count}...")
                product_data = self.data_extractor.extract_product_data(element, i)
                products.append(product_data)
                
                print(f"  Title: {product_data['title']}")
                print(f"  Price: {product_data['price']}")
                print(f"  Rating: {product_data['rating']}")
                print(f"  URL: {product_data['url']}")
                print()
            
            return products
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def scrape_reviews(self, product_url: str, star_filter: Optional[List[int]] = None, max_pages: int = 2) -> List[Dict]:
        """
        Scrape reviews for a specific product with optional star filtering.
        
        Args:
            product_url: URL of the product
            star_filter: List of star ratings to filter by (e.g., [4, 5])
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of review dictionaries
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            # Check session status
            if not self.auth_manager.check_session_status():
                print("⚠️ Session expired - attempting to refresh...")
                if not self.auth_manager.refresh_session():
                    print("❌ Failed to refresh session")
                    return []
            
            # Navigate to product reviews page
            if '/dp/' in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0]
                reviews_url = f"{AMAZON_BASE_URL}/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm"
            else:
                print(f"❌ Invalid product URL format: {product_url}")
                return []
            
            print(f"🌐 Navigating to reviews URL: {reviews_url}")
            
            # Add random delay
            self.data_extractor.add_random_delay()
            
            # Try multiple review URLs
            review_urls = [
                reviews_url,
                f"{AMAZON_BASE_URL}/product-reviews/{asin}/",
                f"{AMAZON_BASE_URL}/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
                f"{AMAZON_BASE_URL}/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent"
            ]
            
            success = False
            for url in review_urls:
                try:
                    print(f"🔄 Trying URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    current_url = self.driver.current_url
                    print(f"📍 Current URL: {current_url}")
                    
                    # Check if we're on a valid reviews page
                    if "product-reviews" in current_url and "signin" not in current_url:
                        print("✅ Successfully reached reviews page")
                        success = True
                        break
                    elif "signin" in current_url:
                        print("❌ Redirected to login page - attempting to refresh session")
                        if self.auth_manager.refresh_session():
                            print("🔄 Session refreshed, retrying...")
                            time.sleep(2)
                            self.driver.get(url)
                            time.sleep(3)
                            current_url = self.driver.current_url
                            if "product-reviews" in current_url and "signin" not in current_url:
                                print("✅ Successfully reached reviews page after session refresh")
                                success = True
                                break
                        else:
                            print("❌ Failed to refresh session")
                            continue
                    else:
                        print("⚠️ Unexpected page, trying next URL")
                        continue
                        
                except Exception as e:
                    print(f"❌ Error with URL {url}: {e}")
                    continue
            
            if not success:
                print("❌ Could not access any review page")
                return []
            
            # Scrape reviews with or without star filtering
            reviews = []
            
            if star_filter:
                # Apply each star filter and collect reviews
                print(f"⭐ Applying star filters: {star_filter}")
                for star in star_filter:
                    print(f"🔍 Applying {star}-star filter...")
                    self.data_extractor.apply_star_filter(star)
                    
                    # Scrape reviews for this star filter
                    star_reviews = self._scrape_review_pages(max_pages)
                    reviews.extend(star_reviews)
                    print(f"📊 Found {len(star_reviews)} reviews for {star}-star filter")
            else:
                # No star filter - scrape all reviews
                print("📊 No star filter - scraping all reviews")
                reviews = self._scrape_review_pages(max_pages)
            
            return reviews
            
        except Exception as e:
            print(f"❌ Review scraping error: {e}")
            return []
    
    def _scrape_review_pages(self, max_pages: int) -> List[Dict]:
        """
        Scrape reviews from multiple pages.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of review dictionaries
        """
        all_reviews = []
        
        for page in range(max_pages):
            print(f"📄 Scraping page {page + 1}/{max_pages}...")
            
            # Find review elements
            review_elements = self.data_extractor.find_elements_by_selectors(
                SELECTORS['review_elements']
            )
            
            if review_elements:
                print(f"📝 Found {len(review_elements)} reviews")
                
                # Extract review data
                page_reviews = []
                for element in review_elements:
                    review_data = self.data_extractor.extract_review_data(element)
                    page_reviews.append(review_data)
                
                all_reviews.extend(page_reviews)
                print(f"✅ Extracted {len(page_reviews)} reviews from page {page + 1}")
            else:
                print(f"⚠️ No reviews found on page {page + 1}")
            
            # Try to go to next page
            if page < max_pages - 1:
                next_btn = self.data_extractor.find_next_page_button()
                if next_btn:
                    try:
                        next_btn.click()
                        time.sleep(3)
                        print(f"➡️ Navigated to page {page + 2}")
                    except Exception as e:
                        print(f"❌ Error navigating to next page: {e}")
                        break
                else:
                    print(f"⚠️ No next page button found, stopping at page {page + 1}")
                    break
        
        return all_reviews
    
    def crawl_amazon(self, keyword: str, top_count: int = 3, star_filter: Optional[List[int]] = None, max_pages: int = 2) -> Dict[str, any]:
        """
        Complete Amazon crawling workflow.
        
        Args:
            keyword: Search keyword
            top_count: Number of products to scrape
            star_filter: List of star ratings to filter by
            max_pages: Maximum pages of reviews per product
            
        Returns:
            Dictionary containing products, reviews, and summary
        """
        print(f"🚀 Starting Amazon crawl for: '{keyword}'")
        print(f"📊 Configuration: {top_count} products, {max_pages} pages per product")
        if star_filter:
            print(f"⭐ Star filter: {star_filter}")
        
        # Search for products
        products = self.search_products(keyword, top_count)
        if not products:
            print("❌ No products found, stopping crawl")
            return {'products': [], 'reviews': [], 'summary': {}}
        
        # Scrape reviews for each product
        all_reviews = []
        for i, product in enumerate(products, 1):
            if product['url'] == 'N/A':
                print(f"⚠️ Skipping product {i} - no valid URL")
                continue
            
            print(f"\n📖 Scraping reviews for product {i}/{len(products)}: {product['title']}")
            reviews = self.scrape_reviews(product['url'], star_filter, max_pages)
            
            # Add product context to reviews
            for review in reviews:
                review['product_title'] = product['title']
                review['product_url'] = product['url']
            
            all_reviews.extend(reviews)
            print(f"✅ Collected {len(reviews)} reviews for product {i}")
        
        # Process and save data
        processed_products = self.data_processor.process_products_data(products, keyword)
        processed_reviews = self.data_processor.process_reviews_data(all_reviews)
        
        # Save data
        filename = f"amazon_reviews_{keyword}"
        
        # Organize products and reviews into nested structure
        organized_data = self.data_processor.organize_products_with_reviews(processed_products, processed_reviews)
        
        saved_files = self.data_processor.save_data(
            organized_data, filename, DEFAULT_SETTINGS['output_format']
        )
        
        # Generate summary
        summary = self.data_processor.get_data_summary_from_organized(organized_data)
        self.data_processor.print_summary(summary)
        
        return {
            'products': processed_products,
            'reviews': processed_reviews,
            'summary': summary,
            'saved_files': saved_files
        }
    
    def close(self):
        """Close the WebDriver and clean up resources."""
        if self.driver:
            self.driver.quit()
            print("🔒 WebDriver closed")
    
    def __enter__(self):
        """Context manager entry."""
        # Ensure WebDriver is initialized when entering context
        if not self.driver:
            self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
