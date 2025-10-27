# Amazon Product Review Crawler

A comprehensive web crawler for Amazon product reviews with support for product search, review filtering, and automated login.

## Features

- **Product Search**: Search Amazon by keyword and get top 3 products
- **Review Scraping**: Scrape user reviews with pagination support
- **Star Rating Filter**: Filter reviews by star rating (1-5 stars)
- **Automated Login**: Login to Amazon account and maintain session
- **Data Export**: Export results to JSON and/or CSV formats
- **Headless Mode**: Run browser in background (configurable)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd webCrawler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your Amazon credentials if you want to use login feature
```

## Usage

### Basic Usage

Search for products and scrape reviews:
```bash
python main.py "wireless headphones"
```

### Advanced Usage

Filter reviews by star rating and scrape more pages:
```bash
python main.py "wireless headphones" --star-filter 5 --max-pages 3
```

Specify output format and directory:
```bash
python main.py "wireless headphones" --output-format json --output-dir results
```

### Command Line Options

- `keyword`: Product keyword to search for (required)
- `--star-filter`: Filter reviews by star rating (1-5)
- `--max-pages`: Maximum number of review pages to scrape (default: 2)
- `--headless`: Run browser in headless mode (default: True)
- `--login`: Login to Amazon account (requires env vars)
- `--output-format`: Output format - json, csv, or both (default: both)
- `--output-dir`: Output directory for saved files (default: output)

## Environment Variables

Create a `.env` file with your Amazon credentials (optional):
```
AMAZON_EMAIL=your_email@example.com
AMAZON_PASSWORD=your_password
```

## Output Data

The crawler extracts the following review data:
- Review text
- Star rating
- Review date
- Reviewer nickname
- Review title
- Product title
- Product URL
- Product rank

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver (automatically managed by webdriver-manager)

## Legal Notice

This tool is for educational and research purposes only. Please respect Amazon's robots.txt and terms of service. Use responsibly and consider rate limiting to avoid overwhelming their servers.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
