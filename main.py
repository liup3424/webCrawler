#!/usr/bin/env python3
"""
Amazon Product Review Crawler
Main CLI interface for crawling Amazon product reviews
"""

import argparse
import os
import sys
from datetime import datetime
from amazon_crawler import AmazonCrawler

def main():
    parser = argparse.ArgumentParser(description='Amazon Product Review Crawler')
    parser.add_argument('keyword', help='Product keyword to search for')
    parser.add_argument('--top-count', type=int, default=3, 
                       help='Number of top products to scrape (default: 3)')
    parser.add_argument('--star-filter', type=str, 
                       help='Filter reviews by star rating(s). Single star: "4" or Multiple stars: "4,5" or "1,2,3" (1-5)')
    parser.add_argument('--max-pages', type=int, default=2, 
                       help='Maximum number of review pages to scrape (default: 2)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--manual-login', action='store_true',
                       help='Manual login mode - opens browser for you to login manually and saves cookies')
    parser.add_argument('--no-auto-login', action='store_true',
                       help='Disable automatic cookie loading (default: auto-load cookies if available)')
    parser.add_argument('--output-format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format for saved data (default: both)')
    parser.add_argument('--output-dir', default=None,
                       help='Output directory for saved files (default: ./output)')
    
    args = parser.parse_args()
    
    # Parse star filter
    star_filter = None
    if args.star_filter:
        try:
            star_list = [int(x.strip()) for x in args.star_filter.split(',')]
            # Validate star ratings (1-5)
            if not all(1 <= star <= 5 for star in star_list):
                print("Error: Star ratings must be between 1 and 5")
                sys.exit(1)
            star_filter = star_list
            print(f"Star filter: {star_filter}")
        except ValueError:
            print("Error: Invalid star filter format. Use: '4' or '4,5' or '1,2,3'")
            sys.exit(1)
    
    # Set default output directory to ./output in current repo
    if args.output_dir is None:
        args.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Determine headless mode
    headless_mode = args.headless
    
    # Initialize crawler
    crawler = AmazonCrawler(headless=headless_mode)
    
    try:
        # Handle login logic
        cookie_file = "amazon_cookies.json"
        
        if args.manual_login:
            # Force manual login (refresh cookies)
            print("Starting manual login process...")
            if not crawler.manual_login_and_save_cookies():
                print("Manual login failed. Continuing without login...")
            else:
                print("Manual login successful!")
                
        elif args.no_auto_login:
            # Skip login entirely
            print("Skipping login (--no-auto-login specified)")
            
        else:
            # Smart cookie detection
            if os.path.exists(cookie_file):
                print("Found existing cookies, loading...")
                if not crawler.load_cookies():
                    print("⚠️  Cookies expired or invalid! Starting manual login...")
                    if not crawler.manual_login_and_save_cookies():
                        print("Manual login failed. Continuing without login...")
                    else:
                        print("Manual login successful!")
                else:
                    print("✅ Cookies loaded successfully!")
            else:
                print("⚠️  No cookies found! Starting manual login...")
                if not crawler.manual_login_and_save_cookies():
                    print("Manual login failed. Continuing without login...")
                else:
                    print("Manual login successful!")
                
        
        # Search for products
        print(f"Searching for products with keyword: '{args.keyword}'")
        products = crawler.search_products(args.keyword, top_count=args.top_count)
        
        if not products:
            print("No products found!")
            return
            
        print(f"Found {len(products)} products:")
        for product in products:
            print(f"  {product['rank']}. {product['title']}")
            print(f"     Price: {product['price']}")
            print(f"     Rating: {product['rating']}")
            print(f"     URL: {product['url']}")
            print()
        
        # Scrape reviews for each product
        all_reviews = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for product in products:
            print(f"Scraping reviews for: {product['title']}")
            
            reviews = crawler.scrape_reviews(
                product['url'], 
                star_filter=star_filter,
                max_pages=args.max_pages
            )
            
            print(f"  Found {len(reviews)} reviews")
            
            # Add product info to each review
            for review in reviews:
                review['product_title'] = product['title']
                review['product_url'] = product['url']
                review['product_rank'] = product['rank']
            
            all_reviews.extend(reviews)
        
        # Save results
        if all_reviews:
            print(f"\nSaving {len(all_reviews)} total reviews...")
            
            if args.output_format in ['json', 'both']:
                json_file = os.path.join(args.output_dir, f'amazon_reviews_{args.keyword}_{timestamp}.json')
                crawler.save_to_json(all_reviews, json_file)
                print(f"Saved to JSON: {json_file}")
            
            if args.output_format in ['csv', 'both']:
                csv_file = os.path.join(args.output_dir, f'amazon_reviews_{args.keyword}_{timestamp}.csv')
                crawler.save_to_csv(all_reviews, csv_file)
                print(f"Saved to CSV: {csv_file}")
        else:
            print("No reviews found to save.")
            
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        crawler.close()

if __name__ == "__main__":
    main()
