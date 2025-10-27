"""
Configuration constants and settings for the Amazon Web Crawler.
"""

# Amazon URLs
AMAZON_BASE_URL = "https://www.amazon.com"
AMAZON_LOGIN_URL = (
    "https://www.amazon.com/ap/signin"
    "?openid.return_to=https%3A%2F%2Fwww.amazon.com%2F"
    "&openid.pape.max_auth_age=0"
    "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
    "&openid.assoc_handle=usflex"
    "&openid.mode=checkid_setup"
    "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
    "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
)

# Cookie settings
COOKIE_FILE = "./amazon_cookies.json"
MANUAL_LOGIN_TIMEOUT = 180  # seconds

# Chrome WebDriver options
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-web-security",
    "--allow-running-insecure-content",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Selectors for different elements
SELECTORS = {
    "product_elements": [
        '[data-component-type="s-search-result"]',
        '.s-result-item',
        '[data-asin]'
    ],
    "product_title": [
        'h2 a span',
        'h2 span',
        '.s-color-base',
        'a[href*="/dp/"] span'
    ],
    "product_url": [
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
    ],
    "product_price": [
        '.a-price-whole',
        '.a-price .a-offscreen',
        '.a-price-range'
    ],
    "product_rating": [
        '.a-icon-alt',
        '[data-hook="rating-out-of-text"]',
        '.a-icon-star-small',
        '.a-icon-star',
        '.a-star-mini',
        '.a-star-small',
        '.a-icon-star-small .a-icon-alt',
        '.a-icon-star .a-icon-alt',
        '.a-star-mini .a-icon-alt',
        '.a-star-small .a-icon-alt',
        '[aria-label*="stars"]',
        '[aria-label*="star"]',
        '.a-icon-star-small[aria-label]',
        '.a-icon-star[aria-label]',
        '.a-star-mini[aria-label]',
        '.a-star-small[aria-label]'
    ],
    "review_elements": [
        '[data-hook="review"]',
        '.review',
        '[data-hook="review-body"]',
        '.a-section.review',
        '.cr-original-review-item'
    ],
    "review_text": [
        '[data-hook="review-body"] span'
    ],
    "review_rating": [
        '[data-hook="review-star-rating"]'
    ],
    "review_date": [
        '[data-hook="review-date"]'
    ],
    "reviewer_name": [
        '[data-hook="review-author"]',
        '.a-profile-name',
        '.review-byline .author',
        '.cr-original-review-item .a-profile-name',
        '[data-hook="review-author"] .a-profile-name'
    ],
    "review_title": [
        '[data-hook="review-title"] span',
        '[data-hook="review-title"]',
        '.review-title',
        '.cr-original-review-item .review-title',
        'a[data-hook="review-title"]',
        '[data-hook="review-title"] a',
        '.a-size-base.review-title',
        '.review-title-text',
        'h3[data-hook="review-title"]',
        '.a-text-bold.review-title'
    ],
    "next_page": [
        '.a-pagination .a-last a',
        '.a-pagination .a-next',
        '[aria-label="Next Page"]',
        '.a-pagination .a-last',
        'a[aria-label="Next Page"]'
    ],
    "star_filter": [
        '[data-hook="review-star-filter-{star}"]',
        'a[href*="filterByStar={star}_star"]',
        'button[data-hook="review-star-filter-{star}"]',
        '[aria-label*="{star} star"]'
    ]
}

# Login indicators
LOGIN_INDICATORS = [
    "hello,",
    "your account",
    "account & lists",
    "orders",
    "prime"
]

# Default settings
DEFAULT_SETTINGS = {
    "top_count": 3,
    "max_pages": 2,
    "headless": True,
    "output_format": "both",
    "output_dir": "output"
}
