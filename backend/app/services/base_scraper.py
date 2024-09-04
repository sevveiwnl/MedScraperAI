"""Base scraper class for web scraping functionality."""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from app.schemas.article import ArticleCreate


logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all web scrapers."""

    def __init__(
        self,
        base_url: str,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the base scraper.

        Args:
            base_url: Base URL for the website
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            headers: Custom headers for requests
        """
        self.base_url = base_url
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries

        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        if headers:
            default_headers.update(headers)

        self.session.headers.update(default_headers)

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.info(f"Fetching page: {url}")

            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Rate limiting
            time.sleep(self.delay)

            return soup

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return None

    def make_absolute_url(self, url: str) -> str:
        """
        Convert relative URL to absolute URL.

        Args:
            url: URL to convert

        Returns:
            Absolute URL
        """
        return urljoin(self.base_url, url)

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace and newlines
        text = " ".join(text.split())

        # Remove common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")

        return text.strip()

    def extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name
        """
        parsed = urlparse(url)
        return parsed.netloc

    @abstractmethod
    def get_article_links(self, max_articles: int = 10) -> List[str]:
        """
        Get article links from the website.

        Args:
            max_articles: Maximum number of articles to get

        Returns:
            List of article URLs
        """
        pass

    @abstractmethod
    def scrape_article(self, url: str) -> Optional[ArticleCreate]:
        """
        Scrape a single article.

        Args:
            url: Article URL to scrape

        Returns:
            ArticleCreate object or None if failed
        """
        pass

    def scrape_articles(
        self, max_articles: int = 10
    ) -> Tuple[List[ArticleCreate], Dict[str, Any]]:
        """
        Scrape multiple articles.

        Args:
            max_articles: Maximum number of articles to scrape

        Returns:
            Tuple of (articles list, statistics dict)
        """
        start_time = time.time()
        articles = []
        failed_urls = []

        logger.info(f"Starting scrape of {max_articles} articles from {self.base_url}")

        # Get article links
        try:
            article_links = self.get_article_links(max_articles)
            logger.info(f"Found {len(article_links)} article links")
        except Exception as e:
            logger.error(f"Failed to get article links: {str(e)}")
            return [], {
                "total_attempted": 0,
                "successful": 0,
                "failed": 0,
                "failed_urls": [],
                "execution_time": time.time() - start_time,
                "error": str(e),
            }

        # Scrape each article
        for i, url in enumerate(article_links, 1):
            try:
                logger.info(f"Scraping article {i}/{len(article_links)}: {url}")

                article = self.scrape_article(url)
                if article:
                    articles.append(article)
                    logger.info(f"Successfully scraped: {article.title[:50]}...")
                else:
                    failed_urls.append(url)
                    logger.warning(f"Failed to scrape article: {url}")

            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                failed_urls.append(url)

        execution_time = time.time() - start_time

        stats = {
            "total_attempted": len(article_links),
            "successful": len(articles),
            "failed": len(failed_urls),
            "failed_urls": failed_urls,
            "execution_time": execution_time,
            "articles_per_second": (
                len(articles) / execution_time if execution_time > 0 else 0
            ),
        }

        logger.info(
            f"Scraping completed: {stats['successful']}/{stats['total_attempted']} articles in {execution_time:.2f}s"
        )

        return articles, stats

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
