"""Scraper tasks for web scraping functionality."""

import logging
from datetime import datetime
from typing import Dict, Any, List

from app.core.celery_app import celery_app
from app.services.scraper_service import scraper_service


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="scraper.scrape_articles")
def scrape_articles_task(
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
        Dict containing scraped articles and statistics
    """
    logger.info(f"Starting scraper task: {scraper_name}")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "current": 0,
            "total": max_articles,
            "status": f"Starting scraper: {scraper_name}",
            "scraper_name": scraper_name,
        },
    )

    try:
        # Perform scraping
        result = scraper_service.scrape_articles(
            scraper_name=scraper_name,
            max_articles=max_articles,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not result["success"]:
            logger.error(f"Scraping failed: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "task_id": self.request.id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Convert ArticleCreate objects to dictionaries for JSON serialization
        articles_data = []
        for article in result["articles"]:
            article_dict = article.dict()
            # Convert datetime to string if present
            if article_dict.get("published_at"):
                article_dict["published_at"] = article_dict["published_at"].isoformat()
            articles_data.append(article_dict)

        # Update task state with completion
        self.update_state(
            state="SUCCESS",
            meta={
                "current": len(articles_data),
                "total": max_articles,
                "status": f"Completed scraping {len(articles_data)} articles",
                "scraper_name": scraper_name,
            },
        )

        logger.info(f"Scraping completed: {len(articles_data)} articles")

        return {
            "success": True,
            "scraper_name": scraper_name,
            "articles": articles_data,
            "statistics": result["statistics"],
            "scraper_info": result["scraper_info"],
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Scraper task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Error: {str(e)}",
                "scraper_name": scraper_name,
            },
        )
        return {
            "success": False,
            "error": str(e),
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="scraper.scrape_single_article")
def scrape_single_article_task(
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
        Dict containing scraped article data
    """
    logger.info(f"Starting single article scraper task: {scraper_name} - {url}")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Scraping article: {url}",
            "scraper_name": scraper_name,
            "url": url,
        },
    )

    try:
        # Perform scraping
        result = scraper_service.scrape_single_article(
            scraper_name=scraper_name,
            url=url,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not result["success"]:
            logger.error(f"Single article scraping failed: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "url": url,
                "task_id": self.request.id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Convert ArticleCreate object to dictionary for JSON serialization
        article_data = None
        if result["article"]:
            article_dict = result["article"].dict()
            # Convert datetime to string if present
            if article_dict.get("published_at"):
                article_dict["published_at"] = article_dict["published_at"].isoformat()
            article_data = article_dict

        # Update task state with completion
        self.update_state(
            state="SUCCESS",
            meta={
                "status": f"Successfully scraped article: {url}",
                "scraper_name": scraper_name,
                "url": url,
            },
        )

        logger.info(f"Single article scraping completed: {url}")

        return {
            "success": True,
            "scraper_name": scraper_name,
            "url": url,
            "article": article_data,
            "scraper_info": result["scraper_info"],
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Single article scraper task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Error: {str(e)}",
                "scraper_name": scraper_name,
                "url": url,
            },
        )
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="scraper.get_article_links")
def get_article_links_task(
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
        Dict containing article links
    """
    logger.info(f"Starting get article links task: {scraper_name}")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Getting article links from: {scraper_name}",
            "scraper_name": scraper_name,
        },
    )

    try:
        # Get article links
        result = scraper_service.get_article_links(
            scraper_name=scraper_name,
            max_articles=max_articles,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not result["success"]:
            logger.error(f"Getting article links failed: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "task_id": self.request.id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Update task state with completion
        self.update_state(
            state="SUCCESS",
            meta={
                "status": f"Found {len(result['links'])} article links",
                "scraper_name": scraper_name,
            },
        )

        logger.info(f"Get article links completed: {len(result['links'])} links")

        return {
            "success": True,
            "scraper_name": scraper_name,
            "links": result["links"],
            "count": result["count"],
            "scraper_info": result["scraper_info"],
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Get article links task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Error: {str(e)}",
                "scraper_name": scraper_name,
            },
        )
        return {
            "success": False,
            "error": str(e),
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="scraper.test_scraper")
def test_scraper_task(
    self,
    scraper_name: str,
) -> Dict[str, Any]:
    """
    Test a scraper by getting a few article links.

    Args:
        scraper_name: Name of the scraper to test

    Returns:
        Dict containing test results
    """
    logger.info(f"Starting scraper test task: {scraper_name}")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Testing scraper: {scraper_name}",
            "scraper_name": scraper_name,
        },
    )

    try:
        # Test scraper by getting a few links
        result = scraper_service.get_article_links(
            scraper_name=scraper_name,
            max_articles=3,
            delay=0.5,
            timeout=15,
            max_retries=1,
        )

        test_results = {
            "links_found": result.get("count", 0),
            "links": result.get("links", [])[:3],  # Show first 3 links
            "error": result.get("error"),
        }

        # Update task state with completion
        self.update_state(
            state="SUCCESS",
            meta={
                "status": f"Test completed - found {test_results['links_found']} links",
                "scraper_name": scraper_name,
            },
        )

        logger.info(f"Scraper test completed: {scraper_name}")

        return {
            "success": result["success"],
            "scraper_name": scraper_name,
            "test_results": test_results,
            "scraper_info": result.get("scraper_info"),
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Scraper test task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Error: {str(e)}",
                "scraper_name": scraper_name,
            },
        )
        return {
            "success": False,
            "error": str(e),
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }
