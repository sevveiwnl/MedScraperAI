"""Article Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class ArticleBase(BaseModel):
    """Base Article schema with common fields."""

    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    content: str = Field(..., min_length=1, description="Full article content")
    summary: Optional[str] = Field(None, description="Article summary")

    author: Optional[str] = Field(None, max_length=200, description="Article author")
    source: str = Field(..., min_length=1, max_length=100, description="Content source")
    url: str = Field(..., description="Article URL")
    published_at: Optional[datetime] = Field(None, description="Publication date")

    # Medical-specific fields
    credibility_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Credibility score (0.0-1.0)"
    )
    category: Optional[str] = Field(
        None, max_length=100, description="Article category"
    )
    tags: Optional[str] = Field(
        None, max_length=500, description="Comma-separated tags"
    )

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @validator("credibility_score")
    def validate_credibility_score(cls, v):
        """Validate credibility score range."""
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Credibility score must be between 0.0 and 1.0")
        return v


class ArticleCreate(ArticleBase):
    """Schema for creating a new article."""

    pass


class ArticleUpdate(BaseModel):
    """Schema for updating an existing article."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = None

    author: Optional[str] = Field(None, max_length=200)
    source: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = None
    published_at: Optional[datetime] = None

    # Medical-specific fields
    credibility_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ArticleResponse(ArticleBase):
    """Schema for article responses."""

    id: int = Field(..., description="Article ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Article(ArticleResponse):
    """Complete Article schema (alias for ArticleResponse)."""

    pass


class ArticleListResponse(BaseModel):
    """Schema for paginated article list responses."""

    articles: list[ArticleResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ArticleSearchResponse(BaseModel):
    """Schema for article search responses."""

    articles: list[ArticleResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
    query: str
    search_fields: list[str]


class ArticleStatsResponse(BaseModel):
    """Schema for article statistics responses."""

    total_articles: int
    recent_articles: int
    average_credibility: float
    high_credibility_articles: int
    sources: list[dict]
    categories: list[dict]
    last_updated: str
    error: Optional[str] = None
