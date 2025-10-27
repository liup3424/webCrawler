"""
Amazon Web Crawler Package

A modular web crawler for Amazon product reviews with authentication,
star filtering, and data export capabilities.
"""

__version__ = "1.0.0"
__author__ = "Amazon Web Crawler Team"

from .crawler import AmazonCrawler
from .auth import AuthManager
from .utils import DataExtractor
from .data import DataProcessor

__all__ = [
    "AmazonCrawler",
    "AuthManager", 
    "DataExtractor",
    "DataProcessor"
]
