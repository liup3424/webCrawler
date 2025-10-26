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
    parser.add_argument('--star-filter', type=int, choices=[1,2,3,4,5], 
                       help='Filter reviews by star rating (1-5)')
    parser.add_argument('--max-pages', type=int, default=2, 
                       help='Maximum number of review pages to scrape (default: 2)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--login', action='store_true',
                       help='Login to Amazon account (requires AMAZON_EMAIL and AMAZON_PASSWORD env vars)')
    parser.add_argument('--output-format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format for saved data (default: both)')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory for saved files (default: output)')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize crawler
    crawler = AmazonCrawler(headless=args.headless)
    
    try:
        # Login if requested
        if args.login:
            email = os.getenv('AMAZON_EMAIL')
            password = os.getenv('AMAZON_PASSWORD')
            
            if not email or not password:
                print("Error: AMAZON_EMAIL and AMAZON_PASSWORD environment variables must be set for login")
                sys.exit(1)
                
            print("Logging into Amazon...")
            if not crawler.login_to_amazon(email, password):
                print("Login failed. Continuing without login...")
            else:
                print("Successfully logged in!")
        
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
                star_filter=args.star_filter,
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
