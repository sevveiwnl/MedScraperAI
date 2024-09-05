"""Article endpoints for managing articles."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import Article
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse,
    ArticleSearchResponse,
    ArticleStatsResponse,
)
from app.services.article_service import ArticleService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    """Get article service instance."""
    return ArticleService(db)


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_data: ArticleCreate,
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Create a new article.

    Args:
        article_data: Article data to create
        article_service: Article service instance

    Returns:
        Created article

    Raises:
        HTTPException: If article creation fails
    """
    try:
        article = article_service.create_article(article_data)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create article. Article with this URL may already exist.",
            )

        return ArticleResponse.from_orm(article)

    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article by ID.

    Args:
        article_id: Article ID
        article_service: Article service instance

    Returns:
        Article data

    Raises:
        HTTPException: If article not found
    """
    article = article_service.get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found",
        )

    return ArticleResponse.from_orm(article)


@router.get("/", response_model=ArticleListResponse)
def get_articles(
    skip: int = Query(0, ge=0, description="Number of articles to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of articles to return"
    ),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author"),
    date_from: Optional[datetime] = Query(
        None, description="Filter by published date from"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter by published date to"
    ),
    min_credibility: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum credibility score"
    ),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get articles with filtering and pagination.

    Args:
        skip: Number of articles to skip
        limit: Maximum number of articles to return
        source: Filter by source
        category: Filter by category
        author: Filter by author
        date_from: Filter by published date from
        date_to: Filter by published date to
        min_credibility: Minimum credibility score
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        article_service: Article service instance

    Returns:
        Paginated list of articles
    """
    try:
        articles, total_count = article_service.get_articles(
            skip=skip,
            limit=limit,
            source=source,
            category=category,
            author=author,
            date_from=date_from,
            date_to=date_to,
            min_credibility=min_credibility,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return ArticleListResponse(
            articles=[ArticleResponse.from_orm(article) for article in articles],
            total=total_count,
            page=skip // limit + 1,
            per_page=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0,
        )

    except Exception as e:
        logger.error(f"Error getting articles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/search/", response_model=ArticleSearchResponse)
def search_articles(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0, description="Number of articles to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of articles to return"
    ),
    search_fields: List[str] = Query(
        default=["title", "content", "summary"],
        description="Fields to search in",
    ),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_credibility: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum credibility score"
    ),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Search articles by text query.

    Args:
        q: Search query
        skip: Number of articles to skip
        limit: Maximum number of articles to return
        search_fields: Fields to search in
        source: Filter by source
        category: Filter by category
        min_credibility: Minimum credibility score
        article_service: Article service instance

    Returns:
        Search results with articles
    """
    try:
        articles, total_count = article_service.search_articles(
            query=q,
            skip=skip,
            limit=limit,
            search_fields=search_fields,
            source=source,
            category=category,
            min_credibility=min_credibility,
        )

        return ArticleSearchResponse(
            articles=[ArticleResponse.from_orm(article) for article in articles],
            total=total_count,
            page=skip // limit + 1,
            per_page=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0,
            query=q,
            search_fields=search_fields,
        )

    except Exception as e:
        logger.error(f"Error searching articles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Update an article.

    Args:
        article_id: Article ID
        article_data: Updated article data
        article_service: Article service instance

    Returns:
        Updated article

    Raises:
        HTTPException: If article not found
    """
    try:
        article = article_service.update_article(article_id, article_data)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found",
            )

        return ArticleResponse.from_orm(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Delete an article.

    Args:
        article_id: Article ID
        article_service: Article service instance

    Raises:
        HTTPException: If article not found
    """
    try:
        success = article_service.delete_article(article_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/bulk", response_model=Dict[str, Any])
def bulk_create_articles(
    articles_data: List[ArticleCreate],
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Create multiple articles in bulk.

    Args:
        articles_data: List of article data
        article_service: Article service instance

    Returns:
        Result summary with created articles count and errors
    """
    try:
        created_articles, errors = article_service.bulk_create_articles(articles_data)

        return {
            "created_count": len(created_articles),
            "total_count": len(articles_data),
            "errors": errors,
            "articles": [
                ArticleResponse.from_orm(article) for article in created_articles
            ],
        }

    except Exception as e:
        logger.error(f"Error bulk creating articles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/stats/summary", response_model=ArticleStatsResponse)
def get_article_statistics(
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article statistics.

    Args:
        article_service: Article service instance

    Returns:
        Article statistics
    """
    try:
        stats = article_service.get_article_statistics()
        return ArticleStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting article statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{article_id}/similar", response_model=List[ArticleResponse])
def get_similar_articles(
    article_id: int,
    limit: int = Query(
        5, ge=1, le=20, description="Maximum number of similar articles to return"
    ),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get articles similar to the given article.

    Args:
        article_id: Article ID to find similar articles for
        limit: Maximum number of similar articles to return
        article_service: Article service instance

    Returns:
        List of similar articles

    Raises:
        HTTPException: If article not found
    """
    try:
        # First check if the article exists
        article = article_service.get_article(article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found",
            )

        similar_articles = article_service.get_similar_articles(article_id, limit)
        return [ArticleResponse.from_orm(article) for article in similar_articles]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar articles for {article_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/by-url/", response_model=ArticleResponse)
def get_article_by_url(
    url: str = Query(..., description="Article URL"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Get article by URL.

    Args:
        url: Article URL
        article_service: Article service instance

    Returns:
        Article data

    Raises:
        HTTPException: If article not found
    """
    try:
        article = article_service.get_article_by_url(url)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with URL '{url}' not found",
            )

        return ArticleResponse.from_orm(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article by URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
