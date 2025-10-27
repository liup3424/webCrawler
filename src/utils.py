"""
Utility functions for data extraction and web scraping.
"""

import time
import random
import urllib.parse
from typing import List, Dict, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .config import SELECTORS


class DataExtractor:
    """Handles data extraction from web elements."""
    
    def __init__(self, driver):
        """Initialize the data extractor with a WebDriver instance."""
        self.driver = driver
    
    def extract_product_data(self, element: WebElement, index: int) -> Dict[str, str]:
        """
        Extract product data from a search result element.
        
        Args:
            element: WebElement containing product information
            index: Index of the product in search results
            
        Returns:
            Dict containing product title, price, rating, and URL
        """
        product_data = {
            'title': 'N/A',
            'price': 'N/A', 
            'rating': 'N/A',
            'url': 'N/A'
        }
        
        # Extract title
        product_data['title'] = self._extract_text_by_selectors(element, SELECTORS['product_title'])
        
        # Extract price
        product_data['price'] = self._extract_text_by_selectors(element, SELECTORS['product_price'])
        
        # Extract rating
        product_data['rating'] = self._extract_product_rating(element)
        
        # Extract URL (with special handling for sponsored links)
        product_data['url'] = self._extract_product_url(element, index)
        
        return product_data
    
    def extract_review_data(self, element: WebElement) -> Dict[str, str]:
        """
        Extract review data from a review element.
        
        Args:
            element: WebElement containing review information
            
        Returns:
            Dict containing review text, rating, date, nickname, and title
        """
        review_data = {}
        
        # Review text
        review_data['review_text'] = self._extract_text_by_selectors(
            element, SELECTORS['review_text']
        )
        
        # Star rating
        review_data['star_rating'] = self._extract_rating(element)
        
        # Review date
        review_data['review_date'] = self._extract_text_by_selectors(
            element, SELECTORS['review_date']
        )
        
        # Reviewer nickname
        review_data['reviewer_nickname'] = self._extract_reviewer_name(element)
        
        # Review title
        review_data['review_title'] = self._extract_review_title(element)
        
        return review_data
    
    def _extract_text_by_selectors(self, element: WebElement, selectors: List[str]) -> str:
        """
        Try multiple selectors to extract text from an element.
        
        Args:
            element: Parent element to search within
            selectors: List of CSS selectors to try
            
        Returns:
            Extracted text or 'N/A' if not found
        """
        for selector in selectors:
            try:
                found_element = element.find_element(By.CSS_SELECTOR, selector)
                text = found_element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return "N/A"
    
    def _extract_product_url(self, element: WebElement, index: int) -> str:
        """
        Extract product URL with special handling for sponsored links.
        
        Args:
            element: Product element
            index: Product index for debugging
            
        Returns:
            Product URL or 'N/A' if not found
        """
        print(f"  Debugging URL extraction for product {index+1}...")
        
        # Try direct URL selectors first
        for i, selector in enumerate(SELECTORS['product_url']):
            try:
                link_element = element.find_element(By.CSS_SELECTOR, selector)
                href = link_element.get_attribute('href')
                
                if href and ('/dp/' in href or '/gp/product/' in href):
                    print(f"    ✅ Found direct URL: {href}")
                    return href
                    
            except Exception as e:
                print(f"    ❌ Selector {i+1} failed: {e}")
                continue
        
        # If no direct URL found, check for sponsored links
        print(f"    ⚠️ No direct URL found, checking for sponsored links...")
        try:
            all_links = element.find_elements(By.TAG_NAME, 'a')
            print(f"    Found {len(all_links)} total links in element")
            
            for link in all_links:
                href = link.get_attribute('href')
                
                if href and 'sspa/click' in href:
                    try:
                        # Decode sponsored URL
                        parsed_url = urllib.parse.urlparse(href)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        
                        if 'url' in query_params:
                            encoded_url = query_params['url'][0]
                            decoded_url = urllib.parse.unquote(encoded_url)
                            
                            if '/dp/' in decoded_url or '/gp/product/' in decoded_url:
                                print(f"    ✅ Extracted URL from sponsored link: {decoded_url}")
                                return decoded_url
                                
                    except Exception as e:
                        print(f"    ❌ Failed to decode sponsored URL: {e}")
                        continue
                        
                elif href and ('/dp/' in href or '/gp/product/' in href):
                    print(f"    ✅ Found direct URL: {href}")
                    return href
                    
        except Exception as e:
            print(f"    ❌ Error processing links: {e}")
        
        return "N/A"
    
    def _extract_product_rating(self, element: WebElement) -> str:
        """Extract product rating with multiple fallback methods."""
        # Try different rating extraction methods
        for selector in SELECTORS['product_rating']:
            try:
                rating_element = element.find_element(By.CSS_SELECTOR, selector)
                
                # Try to get text content first
                rating_text = rating_element.text.strip()
                if rating_text and any(char.isdigit() for char in rating_text):
                    return rating_text
                
                # Try aria-label attribute
                aria_label = rating_element.get_attribute('aria-label')
                if aria_label and any(char.isdigit() for char in aria_label):
                    return aria_label
                
                # Try textContent
                text_content = rating_element.get_attribute('textContent')
                if text_content and any(char.isdigit() for char in text_content):
                    return text_content.strip()
                    
            except:
                continue
        
        return "N/A"
    
    def _extract_rating(self, element: WebElement) -> str:
        """Extract star rating from review element."""
        try:
            rating_element = element.find_element(By.CSS_SELECTOR, '[data-hook="review-star-rating"]')
            rating_text = rating_element.get_attribute('textContent')
            return rating_text.split()[0] if rating_text else "N/A"
        except:
            return "N/A"
    
    def _extract_reviewer_name(self, element: WebElement) -> str:
        """Extract reviewer nickname with multiple fallback selectors."""
        for selector in SELECTORS['reviewer_name']:
            try:
                reviewer_element = element.find_element(By.CSS_SELECTOR, selector)
                name = reviewer_element.text.strip()
                if name:
                    return name
            except:
                continue
        return "N/A"
    
    def _extract_review_title(self, element: WebElement) -> str:
        """Extract review title with multiple fallback selectors."""
        # Try specific title selectors first
        for selector in SELECTORS['review_title']:
            try:
                title_element = element.find_element(By.CSS_SELECTOR, selector)
                title = title_element.text.strip()
                if title:
                    return title
            except:
                continue
        
        # Fallback: look for any text that might be a title
        try:
            all_text_elements = element.find_elements(By.CSS_SELECTOR, '*')
            for text_elem in all_text_elements:
                text = text_elem.text.strip()
                if text and len(text) < 200:
                    # This might be a title
                    return text
        except:
            pass
        
        return "N/A"
    
    def find_elements_by_selectors(self, selectors: List[str]) -> List[WebElement]:
        """
        Find elements using multiple selectors.
        
        Args:
            selectors: List of CSS selectors to try
            
        Returns:
            List of found elements
        """
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except:
                continue
        return []
    
    def find_element_by_selectors(self, selectors: List[str]) -> Optional[WebElement]:
        """
        Find a single element using multiple selectors.
        
        Args:
            selectors: List of CSS selectors to try
            
        Returns:
            Found element or None
        """
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except:
                continue
        return None
    
    def apply_star_filter(self, star: int) -> bool:
        """
        Apply a star filter on Amazon's review page.
        
        Args:
            star: Star rating to filter by (1-5)
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            # Try different star filter selectors
            star_selectors = [
                f'[data-hook="review-star-filter-{star}"]',
                f'a[href*="filterByStar={star}_star"]',
                f'button[data-hook="review-star-filter-{star}"]',
                f'[aria-label*="{star} star"]'
            ]
            
            for selector in star_selectors:
                try:
                    filter_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if filter_element.is_enabled():
                        filter_element.click()
                        time.sleep(2)
                        print(f"✅ Applied {star}-star filter")
                        return True
                except:
                    continue
            
            print(f"⚠️ Could not find {star}-star filter button")
            return False
            
        except Exception as e:
            print(f"❌ Error applying {star}-star filter: {e}")
            return False
    
    def find_next_page_button(self) -> Optional[WebElement]:
        """Find the next page button for pagination."""
        for selector in SELECTORS['next_page']:
            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if next_btn.is_enabled():
                    print(f"Found next page button") #  with selector: {selector}
                    return next_btn
            except:
                continue
        return None
    
    def add_random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0) -> None:
        """Add a random delay to appear more human-like."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
