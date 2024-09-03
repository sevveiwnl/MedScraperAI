"""Article SQLAlchemy model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from app.db.base import Base


class Article(Base):
    """Article model representing scraped medical articles."""

    __tablename__ = "articles"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Content fields
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    # Publication info
    author = Column(String(200), nullable=True)
    source = Column(String(100), nullable=False, index=True)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    published_at = Column(DateTime, nullable=True, index=True)

    # Medical-specific fields
    credibility_score = Column(Float, nullable=True, default=0.0)
    category = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of Article."""
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.title} - {self.source}"
