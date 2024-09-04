"""Scraper service for managing web scraping operations."""

import logging
from typing import Dict, List, Optional, Any, Type

from app.schemas.article import ArticleCreate
from app.services.base_scraper import BaseScraper
from app.services.medical_news_today_scraper import MedicalNewsTodayScraper


logger = logging.getLogger(__name__)


class ScraperService:
    """Service for managing web scraping operations."""

    def __init__(self):
        """Initialize the scraper service."""
        self.scrapers = {
            "medical_news_today": MedicalNewsTodayScraper,
        }

    def get_available_scrapers(self) -> List[str]:
        """
        Get list of available scrapers.

        Returns:
            List of scraper names
        """
        return list(self.scrapers.keys())

    def get_scraper_info(self, scraper_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific scraper.

        Args:
            scraper_name: Name of the scraper

        Returns:
            Scraper information or None if not found
        """
        if scraper_name not in self.scrapers:
            return None

        scraper_class = self.scrapers[scraper_name]

        # Create temporary instance to get base URL
        temp_scraper = scraper_class()

        return {
            "name": scraper_name,
            "class_name": scraper_class.__name__,
            "base_url": temp_scraper.base_url,
            "description": scraper_class.__doc__ or "No description available",
            "source": scraper_name.replace("_", " ").title(),
        }

    def create_scraper(self, scraper_name: str, **kwargs) -> Optional[BaseScraper]:
        """
        Create a scraper instance.

        Args:
            scraper_name: Name of the scraper
            **kwargs: Additional arguments for scraper initialization

        Returns:
            Scraper instance or None if not found
        """
        if scraper_name not in self.scrapers:
            logger.error(f"Scraper '{scraper_name}' not found")
            return None

        scraper_class = self.scrapers[scraper_name]

        try:
            return scraper_class(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create scraper '{scraper_name}': {str(e)}")
            return None

    def scrape_articles(
        self,
        scraper_name: str,
        max_articles: int = 10,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Scrape articles using specified scraper.

        Args:
            scraper_name: Name of the scraper to use
            max_articles: Maximum number of articles to scrape
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary containing scraped articles and statistics
        """
        logger.info(f"Starting scraping operation with {scraper_name}")

        # Validate scraper exists
        if scraper_name not in self.scrapers:
            error_msg = f"Scraper '{scraper_name}' not found. Available scrapers: {list(self.scrapers.keys())}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "articles": [],
                "statistics": {},
            }

        # Create scraper instance
        scraper = self.create_scraper(
            scraper_name,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not scraper:
            error_msg = f"Failed to create scraper '{scraper_name}'"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "articles": [],
                "statistics": {},
            }

        # Perform scraping
        try:
            with scraper:
                articles, statistics = scraper.scrape_articles(max_articles)

                logger.info(f"Scraping completed: {len(articles)} articles scraped")

                return {
                    "success": True,
                    "scraper_name": scraper_name,
                    "articles": articles,
                    "statistics": statistics,
                    "scraper_info": self.get_scraper_info(scraper_name),
                }

        except Exception as e:
            error_msg = f"Scraping failed for '{scraper_name}': {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "articles": [],
                "statistics": {},
            }

    def scrape_single_article(
        self,
        scraper_name: str,
        url: str,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Scrape a single article using specified scraper.

        Args:
            scraper_name: Name of the scraper to use
            url: URL of the article to scrape
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary containing scraped article and status
        """
        logger.info(f"Scraping single article with {scraper_name}: {url}")

        # Validate scraper exists
        if scraper_name not in self.scrapers:
            error_msg = f"Scraper '{scraper_name}' not found"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "url": url,
                "article": None,
            }

        # Create scraper instance
        scraper = self.create_scraper(
            scraper_name,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not scraper:
            error_msg = f"Failed to create scraper '{scraper_name}'"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "url": url,
                "article": None,
            }

        # Perform scraping
        try:
            with scraper:
                article = scraper.scrape_article(url)

                if article:
                    logger.info(
                        f"Successfully scraped article: {article.title[:50]}..."
                    )
                    return {
                        "success": True,
                        "scraper_name": scraper_name,
                        "url": url,
                        "article": article,
                        "scraper_info": self.get_scraper_info(scraper_name),
                    }
                else:
                    logger.warning(f"Failed to scrape article: {url}")
                    return {
                        "success": False,
                        "error": "Failed to extract article content",
                        "scraper_name": scraper_name,
                        "url": url,
                        "article": None,
                    }

        except Exception as e:
            error_msg = f"Error scraping article {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "url": url,
                "article": None,
            }

    def get_article_links(
        self,
        scraper_name: str,
        max_articles: int = 10,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Get article links using specified scraper.

        Args:
            scraper_name: Name of the scraper to use
            max_articles: Maximum number of article links to get
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary containing article links and status
        """
        logger.info(f"Getting article links with {scraper_name}")

        # Validate scraper exists
        if scraper_name not in self.scrapers:
            error_msg = f"Scraper '{scraper_name}' not found"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "links": [],
            }

        # Create scraper instance
        scraper = self.create_scraper(
            scraper_name,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not scraper:
            error_msg = f"Failed to create scraper '{scraper_name}'"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "links": [],
            }

        # Get article links
        try:
            with scraper:
                links = scraper.get_article_links(max_articles)

                logger.info(f"Found {len(links)} article links")

                return {
                    "success": True,
                    "scraper_name": scraper_name,
                    "links": links,
                    "count": len(links),
                    "scraper_info": self.get_scraper_info(scraper_name),
                }

        except Exception as e:
            error_msg = f"Error getting article links: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "scraper_name": scraper_name,
                "links": [],
            }


# Global scraper service instance
scraper_service = ScraperService()
