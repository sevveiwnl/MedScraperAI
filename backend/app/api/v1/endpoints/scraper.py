"""Scraper endpoints for web scraping operations."""

from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.scraper_service import scraper_service


router = APIRouter()


class ScraperInfo(BaseModel):
    """Scraper information model."""

    name: str
    class_name: str
    base_url: str
    description: str
    source: str


class ScraperListResponse(BaseModel):
    """Response model for listing scrapers."""

    scrapers: List[str]
    count: int
    details: List[ScraperInfo]


class ArticleLinksResponse(BaseModel):
    """Response model for article links."""

    success: bool
    scraper_name: str
    links: List[str]
    count: int
    scraper_info: ScraperInfo
    error: str = None


class ScrapeArticlesRequest(BaseModel):
    """Request model for scraping articles."""

    scraper_name: str = Field(..., description="Name of the scraper to use")
    max_articles: int = Field(
        10, ge=1, le=100, description="Maximum number of articles to scrape"
    )
    delay: float = Field(
        1.0, ge=0.1, le=5.0, description="Delay between requests in seconds"
    )
    timeout: int = Field(30, ge=5, le=120, description="Request timeout in seconds")
    max_retries: int = Field(
        3, ge=1, le=10, description="Maximum number of retry attempts"
    )


class ScrapeArticlesResponse(BaseModel):
    """Response model for scraping articles."""

    success: bool
    scraper_name: str
    articles: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    scraper_info: ScraperInfo = None
    error: str = None


class ScrapeArticleRequest(BaseModel):
    """Request model for scraping a single article."""

    scraper_name: str = Field(..., description="Name of the scraper to use")
    url: str = Field(..., description="URL of the article to scrape")
    delay: float = Field(
        1.0, ge=0.1, le=5.0, description="Delay between requests in seconds"
    )
    timeout: int = Field(30, ge=5, le=120, description="Request timeout in seconds")
    max_retries: int = Field(
        3, ge=1, le=10, description="Maximum number of retry attempts"
    )


class ScrapeArticleResponse(BaseModel):
    """Response model for scraping a single article."""

    success: bool
    scraper_name: str
    url: str
    article: Dict[str, Any] = None
    scraper_info: ScraperInfo = None
    error: str = None


@router.get("/", response_model=ScraperListResponse)
async def list_scrapers():
    """
    List all available scrapers.

    Returns:
        List of available scrapers with details
    """
    try:
        scraper_names = scraper_service.get_available_scrapers()
        scraper_details = []

        for name in scraper_names:
            info = scraper_service.get_scraper_info(name)
            if info:
                scraper_details.append(ScraperInfo(**info))

        return ScraperListResponse(
            scrapers=scraper_names,
            count=len(scraper_names),
            details=scraper_details,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list scrapers: {str(e)}"
        )


@router.get("/{scraper_name}/info", response_model=ScraperInfo)
async def get_scraper_info(scraper_name: str):
    """
    Get information about a specific scraper.

    Args:
        scraper_name: Name of the scraper

    Returns:
        Scraper information

    Raises:
        HTTPException: If scraper is not found
    """
    info = scraper_service.get_scraper_info(scraper_name)
    if not info:
        raise HTTPException(
            status_code=404, detail=f"Scraper '{scraper_name}' not found"
        )

    return ScraperInfo(**info)


@router.get("/{scraper_name}/links", response_model=ArticleLinksResponse)
async def get_article_links(
    scraper_name: str,
    max_articles: int = Query(
        10, ge=1, le=100, description="Maximum number of article links to get"
    ),
    delay: float = Query(
        1.0, ge=0.1, le=5.0, description="Delay between requests in seconds"
    ),
    timeout: int = Query(30, ge=5, le=120, description="Request timeout in seconds"),
    max_retries: int = Query(
        3, ge=1, le=10, description="Maximum number of retry attempts"
    ),
):
    """
    Get article links using specified scraper.

    Args:
        scraper_name: Name of the scraper to use
        max_articles: Maximum number of article links to get
        delay: Delay between requests in seconds
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        List of article links

    Raises:
        HTTPException: If scraper is not found or operation fails
    """
    try:
        result = scraper_service.get_article_links(
            scraper_name=scraper_name,
            max_articles=max_articles,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return ArticleLinksResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get article links: {str(e)}"
        )


@router.post("/scrape", response_model=ScrapeArticlesResponse)
async def scrape_articles(request: ScrapeArticlesRequest):
    """
    Scrape articles using specified scraper.

    Args:
        request: Scraping request parameters

    Returns:
        Scraped articles and statistics

    Raises:
        HTTPException: If scraper is not found or operation fails
    """
    try:
        result = scraper_service.scrape_articles(
            scraper_name=request.scraper_name,
            max_articles=request.max_articles,
            delay=request.delay,
            timeout=request.timeout,
            max_retries=request.max_retries,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Convert ArticleCreate objects to dictionaries
        articles_data = []
        for article in result["articles"]:
            article_dict = article.dict()
            # Convert datetime to string if present
            if article_dict.get("published_at"):
                article_dict["published_at"] = article_dict["published_at"].isoformat()
            articles_data.append(article_dict)

        result["articles"] = articles_data
        return ScrapeArticlesResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scrape articles: {str(e)}"
        )


@router.post("/scrape/single", response_model=ScrapeArticleResponse)
async def scrape_single_article(request: ScrapeArticleRequest):
    """
    Scrape a single article using specified scraper.

    Args:
        request: Single article scraping request parameters

    Returns:
        Scraped article data

    Raises:
        HTTPException: If scraper is not found or operation fails
    """
    try:
        result = scraper_service.scrape_single_article(
            scraper_name=request.scraper_name,
            url=request.url,
            delay=request.delay,
            timeout=request.timeout,
            max_retries=request.max_retries,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Convert ArticleCreate object to dictionary
        if result["article"]:
            article_dict = result["article"].dict()
            # Convert datetime to string if present
            if article_dict.get("published_at"):
                article_dict["published_at"] = article_dict["published_at"].isoformat()
            result["article"] = article_dict

        return ScrapeArticleResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scrape article: {str(e)}"
        )


@router.get("/{scraper_name}/test")
async def test_scraper(scraper_name: str):
    """
    Test a scraper by getting a few article links.

    Args:
        scraper_name: Name of the scraper to test

    Returns:
        Test results

    Raises:
        HTTPException: If scraper is not found or test fails
    """
    try:
        result = scraper_service.get_article_links(
            scraper_name=scraper_name,
            max_articles=3,
            delay=0.5,
            timeout=15,
            max_retries=1,
        )

        return {
            "success": result["success"],
            "scraper_name": scraper_name,
            "test_results": {
                "links_found": result.get("count", 0),
                "links": result.get("links", [])[:3],  # Show first 3 links
                "error": result.get("error"),
            },
            "scraper_info": result.get("scraper_info"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test scraper: {str(e)}")
