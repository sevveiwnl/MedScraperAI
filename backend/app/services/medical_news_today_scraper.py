"""Medical News Today scraper implementation."""

import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.schemas.article import ArticleCreate
from app.services.base_scraper import BaseScraper


logger = logging.getLogger(__name__)


class MedicalNewsTodayScraper(BaseScraper):
    """Scraper for Medical News Today website."""

    def __init__(self, delay: float = 1.0, timeout: int = 30, max_retries: int = 3):
        """
        Initialize Medical News Today scraper.

        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            base_url="https://www.medicalnewstoday.com",
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

    def get_article_links(self, max_articles: int = 10) -> List[str]:
        """
        Get article links from Medical News Today.

        Args:
            max_articles: Maximum number of articles to get

        Returns:
            List of article URLs
        """
        logger.info(
            f"Fetching article links from Medical News Today (max: {max_articles})"
        )

        # Try multiple pages to get enough articles
        article_links = []
        pages_to_try = [
            "/",  # Homepage
            "/news",  # News section
            "/articles",  # Articles section
        ]

        for page_path in pages_to_try:
            if len(article_links) >= max_articles:
                break

            page_url = urljoin(self.base_url, page_path)
            soup = self.get_page(page_url)

            if not soup:
                continue

            # Find article links using various selectors
            link_selectors = [
                'a[href*="/articles/"]',
                'a[href*="/news/"]',
                ".css-1a8t25n a",  # Common article link class
                "article a",
                ".article-link",
                "h2 a",
                "h3 a",
            ]

            for selector in link_selectors:
                links = soup.select(selector)

                for link in links:
                    href = link.get("href")
                    if not href:
                        continue

                    # Make absolute URL
                    absolute_url = urljoin(self.base_url, href)

                    # Filter for article URLs
                    if (
                        self._is_article_url(absolute_url)
                        and absolute_url not in article_links
                    ):
                        article_links.append(absolute_url)

                        if len(article_links) >= max_articles:
                            break

                if len(article_links) >= max_articles:
                    break

        logger.info(f"Found {len(article_links)} article links")
        return article_links[:max_articles]

    def _is_article_url(self, url: str) -> bool:
        """
        Check if URL is an article URL.

        Args:
            url: URL to check

        Returns:
            True if URL is an article URL
        """
        # Medical News Today article patterns
        article_patterns = [
            r"/articles/\d+",
            r"/news/\d+",
            r"/articles/[a-zA-Z0-9-]+",
            r"/news/[a-zA-Z0-9-]+",
        ]

        for pattern in article_patterns:
            if re.search(pattern, url):
                return True

        return False

    def scrape_article(self, url: str) -> Optional[ArticleCreate]:
        """
        Scrape a single article from Medical News Today.

        Args:
            url: Article URL to scrape

        Returns:
            ArticleCreate object or None if failed
        """
        logger.info(f"Scraping article: {url}")

        soup = self.get_page(url)
        if not soup:
            return None

        try:
            # Extract title
            title = self._extract_title(soup)
            if not title:
                logger.warning(f"Could not extract title from {url}")
                return None

            # Extract content
            content = self._extract_content(soup)
            if not content:
                logger.warning(f"Could not extract content from {url}")
                return None

            # Extract other fields
            author = self._extract_author(soup)
            published_at = self._extract_published_date(soup)
            summary = self._extract_summary(soup)
            category = self._extract_category(soup)

            # Create article object
            article = ArticleCreate(
                title=title,
                content=content,
                summary=summary,
                author=author,
                source="Medical News Today",
                url=url,
                published_at=published_at,
                category=category,
                credibility_score=8.5,  # Medical News Today is generally credible
            )

            logger.info(f"Successfully scraped article: {title[:50]}...")
            return article

        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title."""
        # Try various title selectors
        title_selectors = [
            "h1",
            ".css-1oez2o4",  # Common title class
            '[data-testid="article-title"]',
            "title",
            ".article-title",
            ".entry-title",
        ]

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = self.clean_text(title_elem.get_text())
                if title and len(title) > 5:  # Ensure it's a real title
                    return title

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content."""
        # Try various content selectors
        content_selectors = [
            ".css-16pgf7i",  # Common content class
            '[data-testid="article-body"]',
            ".article-content",
            ".entry-content",
            ".post-content",
            "article",
            ".content",
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select(
                    "script, style, .ad, .advertisement, .social-share"
                ):
                    unwanted.decompose()

                content = self.clean_text(content_elem.get_text())
                if content and len(content) > 100:  # Ensure it's substantial content
                    return content

        # Fallback: try to get all paragraphs
        paragraphs = soup.select("p")
        if paragraphs:
            content_parts = []
            for p in paragraphs:
                text = self.clean_text(p.get_text())
                if text and len(text) > 20:  # Filter out short paragraphs
                    content_parts.append(text)

            if content_parts:
                return " ".join(content_parts)

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        # Try various author selectors
        author_selectors = [
            '[data-testid="author-name"]',
            ".css-1c5j5g7",  # Common author class
            ".author-name",
            ".byline",
            ".author",
            'span[class*="author"]',
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = self.clean_text(author_elem.get_text())
                if author and len(author) > 2:
                    # Clean up author name
                    author = re.sub(
                        r"^(by|written by|author:)\s*", "", author, flags=re.IGNORECASE
                    )
                    return author

        return None

    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract article published date."""
        # Try various date selectors
        date_selectors = [
            '[data-testid="publish-date"]',
            "time[datetime]",
            ".css-1e3j7ww",  # Common date class
            ".publish-date",
            ".date",
            ".published",
        ]

        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                # Try to get datetime attribute first
                datetime_attr = date_elem.get("datetime")
                if datetime_attr:
                    try:
                        return datetime.fromisoformat(
                            datetime_attr.replace("Z", "+00:00")
                        )
                    except:
                        pass

                # Try to parse text content
                date_text = self.clean_text(date_elem.get_text())
                if date_text:
                    try:
                        # Common date formats
                        date_formats = [
                            "%Y-%m-%d",
                            "%B %d, %Y",
                            "%b %d, %Y",
                            "%d %B %Y",
                            "%d %b %Y",
                        ]

                        for fmt in date_formats:
                            try:
                                return datetime.strptime(date_text, fmt)
                            except:
                                continue
                    except:
                        pass

        return None

    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article summary."""
        # Try various summary selectors
        summary_selectors = [
            '[data-testid="article-summary"]',
            ".css-1k8dj5p",  # Common summary class
            ".article-summary",
            ".summary",
            ".excerpt",
            ".lead",
            ".intro",
        ]

        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                summary = self.clean_text(summary_elem.get_text())
                if summary and len(summary) > 20:
                    return summary

        return None

    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article category."""
        # Try various category selectors
        category_selectors = [
            '[data-testid="category"]',
            ".css-1r5nwz4",  # Common category class
            ".category",
            ".tag",
            ".section",
            "nav a",
            ".breadcrumb a",
        ]

        for selector in category_selectors:
            category_elem = soup.select_one(selector)
            if category_elem:
                category = self.clean_text(category_elem.get_text())
                if category and len(category) > 2:
                    return category

        return None
