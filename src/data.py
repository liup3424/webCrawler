"""
Data processing and export functions for Amazon Web Crawler.
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

from .config import DEFAULT_SETTINGS


class DataProcessor:
    """Handles data processing and export operations."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the data processor.
        
        Args:
            output_dir: Directory to save output files (defaults to 'output')
        """
        self.output_dir = output_dir or DEFAULT_SETTINGS['output_dir']
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created output directory: {self.output_dir}")
    
    def save_to_json(self, data: List[Dict], filename: str) -> str:
        """
        Save data to JSON file.
        
        Args:
            data: List of dictionaries to save
            filename: Name of the file (without extension)
            
        Returns:
            Full path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.output_dir, f"{filename}_{timestamp}.json")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Data saved to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving JSON file: {e}")
            raise
    
    def save_to_csv(self, data: List[Dict], filename: str) -> str:
        """
        Save data to CSV file.
        
        Args:
            data: List of dictionaries to save
            filename: Name of the file (without extension)
            
        Returns:
            Full path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.output_dir, f"{filename}_{timestamp}.csv")
        
        try:
            if not data:
                print("⚠️ No data to save to CSV")
                return filepath
            
            # Convert to DataFrame for better CSV handling
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            print(f"💾 Data saved to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving CSV file: {e}")
            raise
    
    def save_data(self, data: List[Dict], filename: str, format_type: str = "both") -> Dict[str, str]:
        """
        Save data in specified format(s).
        
        Args:
            data: List of dictionaries to save
            filename: Name of the file (without extension)
            format_type: Format to save ('json', 'csv', or 'both')
            
        Returns:
            Dictionary with file paths for saved formats
        """
        saved_files = {}
        
        if format_type in ['json', 'both']:
            try:
                json_path = self.save_to_json(data, filename)
                saved_files['json'] = json_path
            except Exception as e:
                print(f"❌ Failed to save JSON: {e}")
        
        if format_type in ['csv', 'both']:
            try:
                csv_path = self.save_to_csv(data, filename)
                saved_files['csv'] = csv_path
            except Exception as e:
                print(f"❌ Failed to save CSV: {e}")
        
        return saved_files
    
    def process_products_data(self, products: List[Dict], keyword: str) -> List[Dict]:
        """
        Process and clean product data.
        
        Args:
            products: List of product dictionaries
            keyword: Search keyword for context
            
        Returns:
            Processed list of products
        """
        processed_products = []
        
        for i, product in enumerate(products, 1):
            processed_product = {
                'product_id': i,
                'search_keyword': keyword,
                'title': product.get('title', 'N/A'),
                'price': product.get('price', 'N/A'),
                'rating': product.get('rating', 'N/A'),
                'url': product.get('url', 'N/A'),
                'scraped_at': datetime.now().isoformat()
            }
            processed_products.append(processed_product)
        
        return processed_products
    
    def process_reviews_data(self, reviews: List[Dict], product_info: Dict = None) -> List[Dict]:
        """
        Process and clean review data.
        
        Args:
            reviews: List of review dictionaries
            product_info: Product information for context (optional, reviews may already have this)
            
        Returns:
            Processed list of reviews
        """
        processed_reviews = []
        
        for i, review in enumerate(reviews, 1):
            processed_review = {
                'review_id': i,
                'product_title': review.get('product_title', product_info.get('title', 'N/A') if product_info else 'N/A'),
                'product_url': review.get('product_url', product_info.get('url', 'N/A') if product_info else 'N/A'),
                'review_text': review.get('review_text', 'N/A'),
                'star_rating': review.get('star_rating', 'N/A'),
                'review_date': review.get('review_date', 'N/A'),
                'reviewer_nickname': review.get('reviewer_nickname', 'N/A'),
                'review_title': review.get('review_title', 'N/A'),
                'scraped_at': datetime.now().isoformat()
            }
            processed_reviews.append(processed_review)
        
        return processed_reviews
    
    def organize_products_with_reviews(self, products: List[Dict], reviews: List[Dict]) -> Dict[str, Dict]:
        """
        Organize products and reviews into a nested structure by product and star rating.
        
        Args:
            products: List of product dictionaries
            reviews: List of review dictionaries
            
        Returns:
            Dictionary with products as keys and nested data structure as values
        """
        organized_data = {}
        
        # Create product entries
        for i, product in enumerate(products, 1):
            product_key = f"product_{i}"
            organized_data[product_key] = {
                "product_data": product,
                "reviews": {}
            }
        
        # Group reviews by product and star rating
        for review in reviews:
            # Find which product this review belongs to
            product_title = review.get('product_title', '')
            product_url = review.get('product_url', '')
            
            # Match review to product by title or URL
            matched_product_key = None
            for product_key, product_info in organized_data.items():
                product_data = product_info['product_data']
                if (product_title == product_data.get('title', '') or 
                    product_url == product_data.get('url', '')):
                    matched_product_key = product_key
                    break
            
            if matched_product_key:
                # Extract star rating
                star_rating = review.get('star_rating', 'N/A')
                if star_rating != 'N/A':
                    # Clean star rating (e.g., "4.0" -> "4")
                    try:
                        star_int = int(float(star_rating))
                        star_key = str(star_int)
                    except:
                        star_key = star_rating
                else:
                    star_key = 'unknown'
                
                # Add review to the appropriate star rating group
                if star_key not in organized_data[matched_product_key]['reviews']:
                    organized_data[matched_product_key]['reviews'][star_key] = []
                
                organized_data[matched_product_key]['reviews'][star_key].append(review)
        
        return organized_data
    
    def get_data_summary_from_organized(self, organized_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Generate a summary from organized product and review data.
        
        Args:
            organized_data: Organized data structure with products and reviews
            
        Returns:
            Summary statistics
        """
        total_products = len(organized_data)
        total_reviews = 0
        star_distribution = {}
        
        for product_key, product_info in organized_data.items():
            reviews = product_info.get('reviews', {})
            for star_rating, review_list in reviews.items():
                review_count = len(review_list)
                total_reviews += review_count
                
                if star_rating not in star_distribution:
                    star_distribution[star_rating] = 0
                star_distribution[star_rating] += review_count
        
        summary = {
            'total_products': total_products,
            'total_reviews': total_reviews,
            'star_distribution': star_distribution,
            'scraped_at': datetime.now().isoformat()
        }
        
        return summary
    
    def get_data_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Generate a summary of the scraped data.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            Summary statistics
        """
        if not data:
            return {
                'total_items': 0,
                'products': 0,
                'reviews': 0,
                'scraped_at': datetime.now().isoformat()
            }
        
        # Count by type if data has type field
        if data and 'type' in data[0]:
            products = len([item for item in data if item.get('type') == 'product'])
            reviews = len([item for item in data if item.get('type') == 'review'])
        else:
            # Assume all items are reviews if no type field
            products = 0
            reviews = len(data)
        
        summary = {
            'total_items': len(data),
            'products': products,
            'reviews': reviews,
            'scraped_at': datetime.now().isoformat()
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print a formatted summary of the scraped data."""
        print("\n" + "="*50)
        print("📊 SCRAPING SUMMARY")
        print("="*50)
        print(f"📦 Total Products: {summary.get('total_products', 0)}")
        print(f"⭐ Total Reviews: {summary.get('total_reviews', 0)}")
        
        # Print star distribution if available
        star_distribution = summary.get('star_distribution', {})
        if star_distribution:
            print("\n⭐ Star Distribution:")
            for star, count in sorted(star_distribution.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
                print(f"  {star} stars: {count} reviews")
        
        print(f"🕒 Scraped At: {summary.get('scraped_at', 'N/A')}")
        print("="*50)
