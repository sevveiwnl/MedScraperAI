"""Summarizer endpoints for text summarization operations."""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.summarizer_service import SummarizerService, SummarizerType


logger = logging.getLogger(__name__)
router = APIRouter()


class SummarizeTextRequest(BaseModel):
    """Request model for text summarization."""

    text: str = Field(..., min_length=100, description="Text to summarize")
    max_length: int = Field(
        200, ge=50, le=500, description="Maximum summary length in words"
    )
    min_length: int = Field(
        50, ge=20, le=300, description="Minimum summary length in words"
    )
    style: str = Field(
        "professional", description="Summary style (professional, casual, academic)"
    )
    focus: str = Field(
        "medical", description="Summary focus (medical, general, technical)"
    )
    summarizer_type: SummarizerType = Field(
        SummarizerType.OPENAI, description="Type of summarizer to use"
    )


class SummarizeArticleRequest(BaseModel):
    """Request model for article summarization."""

    title: str = Field(..., min_length=5, description="Article title")
    content: str = Field(..., min_length=100, description="Article content")
    author: Optional[str] = Field(None, description="Article author")
    source: Optional[str] = Field(None, description="Article source")
    max_length: int = Field(
        150, ge=50, le=500, description="Maximum summary length in words"
    )
    min_length: int = Field(
        50, ge=20, le=300, description="Minimum summary length in words"
    )
    style: str = Field(
        "professional", description="Summary style (professional, casual, academic)"
    )
    focus: str = Field(
        "medical", description="Summary focus (medical, general, technical)"
    )
    summarizer_type: SummarizerType = Field(
        SummarizerType.OPENAI, description="Type of summarizer to use"
    )


class BatchSummarizeRequest(BaseModel):
    """Request model for batch text summarization."""

    texts: List[str] = Field(
        ..., min_items=1, max_items=10, description="List of texts to summarize"
    )
    max_length: int = Field(
        200, ge=50, le=500, description="Maximum summary length in words"
    )
    min_length: int = Field(
        50, ge=20, le=300, description="Minimum summary length in words"
    )
    style: str = Field(
        "professional", description="Summary style (professional, casual, academic)"
    )
    focus: str = Field(
        "medical", description="Summary focus (medical, general, technical)"
    )
    summarizer_type: SummarizerType = Field(
        SummarizerType.OPENAI, description="Type of summarizer to use"
    )


class SummaryResponse(BaseModel):
    """Response model for summarization."""

    success: bool
    summary: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


class BatchSummaryResponse(BaseModel):
    """Response model for batch summarization."""

    results: List[SummaryResponse]
    total_count: int
    success_count: int
    error_count: int
    batch_metadata: Dict[str, Any]


class SummarizerInfoResponse(BaseModel):
    """Response model for summarizer service information."""

    summarizer_type: str
    available_types: List[str]
    openai_available: bool
    bart_available: bool
    service_name: str
    version: str
    timestamp: str


@router.post("/text", response_model=SummaryResponse)
async def summarize_text(request: SummarizeTextRequest):
    """
    Summarize a text using the specified summarizer.

    Args:
        request: Text summarization request

    Returns:
        Summary result with metadata

    Raises:
        HTTPException: If summarization fails
    """
    try:
        # Create summarizer service
        summarizer = SummarizerService(request.summarizer_type)

        # Generate summary
        result = summarizer.summarize_text(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            style=request.style,
            focus=request.focus,
        )

        return SummaryResponse(**result)

    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize text: {str(e)}",
        )


@router.post("/article", response_model=SummaryResponse)
async def summarize_article(request: SummarizeArticleRequest):
    """
    Summarize an article using the specified summarizer.

    Args:
        request: Article summarization request

    Returns:
        Summary result with metadata

    Raises:
        HTTPException: If summarization fails
    """
    try:
        # Create summarizer service
        summarizer = SummarizerService(request.summarizer_type)

        # Generate summary
        result = summarizer.summarize_article(
            title=request.title,
            content=request.content,
            author=request.author,
            source=request.source,
            max_length=request.max_length,
            min_length=request.min_length,
            style=request.style,
            focus=request.focus,
        )

        return SummaryResponse(**result)

    except Exception as e:
        logger.error(f"Error summarizing article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize article: {str(e)}",
        )


@router.post("/batch", response_model=BatchSummaryResponse)
async def batch_summarize(request: BatchSummarizeRequest):
    """
    Summarize multiple texts in batch using the specified summarizer.

    Args:
        request: Batch summarization request

    Returns:
        Batch summary results with metadata

    Raises:
        HTTPException: If batch summarization fails
    """
    try:
        # Create summarizer service
        summarizer = SummarizerService(request.summarizer_type)

        # Generate summaries
        results = summarizer.batch_summarize(
            texts=request.texts,
            max_length=request.max_length,
            min_length=request.min_length,
            style=request.style,
            focus=request.focus,
        )

        # Convert to response format
        response_results = [SummaryResponse(**result) for result in results]

        # Calculate stats
        success_count = sum(1 for r in results if r["success"])
        error_count = len(results) - success_count

        return BatchSummaryResponse(
            results=response_results,
            total_count=len(results),
            success_count=success_count,
            error_count=error_count,
            batch_metadata={
                "summarizer_type": request.summarizer_type.value,
                "total_texts": len(request.texts),
                "success_rate": success_count / len(results) if results else 0,
                "average_input_length": sum(len(text) for text in request.texts)
                / len(request.texts),
            },
        )

    except Exception as e:
        logger.error(f"Error batch summarizing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch summarize: {str(e)}",
        )


@router.get("/info", response_model=SummarizerInfoResponse)
async def get_summarizer_info():
    """
    Get information about the summarizer service.

    Returns:
        Summarizer service information

    Raises:
        HTTPException: If service info retrieval fails
    """
    try:
        # Create summarizer service (default type)
        summarizer = SummarizerService()

        # Get service info
        info = summarizer.get_service_info()

        return SummarizerInfoResponse(**info)

    except Exception as e:
        logger.error(f"Error getting summarizer info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summarizer info: {str(e)}",
        )


@router.get("/types", response_model=List[str])
async def get_available_summarizer_types():
    """
    Get list of available summarizer types.

    Returns:
        List of available summarizer types

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        return [t.value for t in SummarizerType]

    except Exception as e:
        logger.error(f"Error getting summarizer types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summarizer types: {str(e)}",
        )


@router.post("/article/{article_id}/summary", response_model=SummaryResponse)
async def summarize_article_by_id(
    article_id: int,
    summarizer_type: SummarizerType = SummarizerType.OPENAI,
    max_length: int = 150,
    min_length: int = 50,
    style: str = "professional",
    focus: str = "medical",
):
    """
    Generate a summary for an existing article by ID.

    Args:
        article_id: ID of the article to summarize
        summarizer_type: Type of summarizer to use
        max_length: Maximum summary length in words
        min_length: Minimum summary length in words
        style: Summary style
        focus: Summary focus

    Returns:
        Summary result with metadata

    Raises:
        HTTPException: If article not found or summarization fails
    """
    try:
        # Import here to avoid circular imports
        from app.services.article_service import ArticleService
        from app.db.session import get_db

        # Get article from database
        db_session = next(get_db())
        article_service = ArticleService(db_session)

        article = article_service.get_article(article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article with ID {article_id} not found",
            )

        # Create summarizer service
        summarizer = SummarizerService(summarizer_type)

        # Generate summary
        result = summarizer.summarize_article(
            title=article.title,
            content=article.content,
            author=article.author,
            source=article.source,
            max_length=max_length,
            min_length=min_length,
            style=style,
            focus=focus,
        )

        # Add article ID to metadata
        if result["success"]:
            result["metadata"]["article_id"] = article_id
            result["metadata"]["article_url"] = article.url

        db_session.close()
        return SummaryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing article {article_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize article: {str(e)}",
        )
