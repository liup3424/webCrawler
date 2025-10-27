#!/usr/bin/env python3
"""
Amazon Product Review Crawler
Main CLI interface for crawling Amazon product reviews
"""

import argparse
import os
import sys
from datetime import datetime
from src import AmazonCrawler
from src.config import DEFAULT_SETTINGS, COOKIE_FILE


def main():
    parser = argparse.ArgumentParser(description='Amazon Product Review Crawler')
    parser.add_argument('keyword', help='Product keyword to search for')
    parser.add_argument('--top-count', type=int, default=DEFAULT_SETTINGS['top_count'], 
                       help=f'Number of top products to scrape (default: {DEFAULT_SETTINGS["top_count"]})')
    parser.add_argument('--star-filter', type=str, 
                       help='Filter reviews by star rating(s). Single star: "4" or Multiple stars: "4,5" or "1,2,3" (1-5)')
    parser.add_argument('--max-pages', type=int, default=DEFAULT_SETTINGS['max_pages'], 
                       help=f'Maximum number of review pages to scrape (default: {DEFAULT_SETTINGS["max_pages"]})')
    parser.add_argument('--headless', action='store_true', default=DEFAULT_SETTINGS['headless'],
                       help=f'Run browser in headless mode (default: {DEFAULT_SETTINGS["headless"]})')
    parser.add_argument('--manual-login', action='store_true',
                       help='Manual login mode - opens browser for you to login manually and saves cookies')
    parser.add_argument('--output-format', choices=['json', 'csv', 'both'], default=DEFAULT_SETTINGS['output_format'],
                       help=f'Output format for saved data (default: {DEFAULT_SETTINGS["output_format"]})')
    parser.add_argument('--output-dir', default=None,
                       help=f'Output directory for saved files (default: {DEFAULT_SETTINGS["output_dir"]})')
    
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
            print(f"⭐ Star filter: {star_filter}")
        except ValueError:
            print("Error: Invalid star filter format. Use: '4' or '4,5' or '1,2,3'")
            sys.exit(1)
    
    # Set default output directory
    if args.output_dir is None:
        args.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_SETTINGS['output_dir'])
    
    # Determine headless mode
    headless_mode = args.headless
    
    print("🚀 Amazon Product Review Crawler")
    print("=" * 50)
    print(f"🔍 Keyword: {args.keyword}")
    print(f"📦 Products: {args.top_count}")
    print(f"📄 Max Pages: {args.max_pages}")
    print(f"🖥️  Headless: {headless_mode}")
    print(f"📁 Output Dir: {args.output_dir}")
    print(f"💾 Output Format: {args.output_format}")
    if star_filter:
        print(f"⭐ Star Filter: {star_filter}")
    print("=" * 50)
    
    # Initialize crawler with context manager
    with AmazonCrawler(headless=headless_mode, output_dir=args.output_dir) as crawler:
        try:
            # Handle authentication
            handle_authentication(crawler, args)
            
            # Run the complete crawling workflow
            result = crawler.crawl_amazon(
                keyword=args.keyword,
                top_count=args.top_count,
                star_filter=star_filter,
                max_pages=args.max_pages
            )
            
            # Print final results
            print("\n🎉 Crawling completed successfully!")
            print(f"📦 Products found: {len(result['products'])}")
            print(f"⭐ Reviews collected: {len(result['reviews'])}")
            
            if result['saved_files']:
                print("\n💾 Files saved:")
                for format_type, filepath in result['saved_files'].items():
                    print(f"  {format_type.upper()}: {filepath}")
            
        except KeyboardInterrupt:
            print("\n⚠️ Crawling interrupted by user.")
        except Exception as e:
            print(f"❌ Error during crawling: {e}")
            sys.exit(1)


def handle_authentication(crawler, args):
    """
    Handle authentication logic based on command line arguments.
    
    Args:
        crawler: AmazonCrawler instance
        args: Parsed command line arguments
    """
    # Ensure WebDriver is initialized before authentication
    if not crawler.driver:
        crawler.setup_driver()
    
    cookie_file = COOKIE_FILE
    
    if args.manual_login:
        # Force manual login (refresh cookies)
        print("🔐 Starting manual login process...")
        if not crawler.auth_manager.manual_login_and_save_cookies():
            print("❌ Manual login failed. Continuing without login...")
        else:
            print("✅ Manual login successful!")
            
    else:
        # Smart cookie detection
        if os.path.exists(cookie_file):
            print("🍪 Found existing cookies, loading...")
            if not crawler.auth_manager.load_cookies():
                print("⚠️ Cookies expired or invalid! Starting manual login...")
                if not crawler.auth_manager.manual_login_and_save_cookies():
                    print("❌ Manual login failed. Continuing without login...")
                else:
                    print("✅ Manual login successful!")
            else:
                print("✅ Cookies loaded successfully!")
        else:
            print("⚠️ No cookies found! Starting manual login...")
            if not crawler.auth_manager.manual_login_and_save_cookies():
                print("❌ Manual login failed. Continuing without login...")
            else:
                print("✅ Manual login successful!")


if __name__ == "__main__":
    main()