"""Article service for managing article operations."""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import IntegrityError

from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate


logger = logging.getLogger(__name__)


class ArticleService:
    """Service for managing article operations."""

    def __init__(self, db: Session):
        """
        Initialize the article service.

        Args:
            db: Database session
        """
        self.db = db

    def create_article(self, article_data: ArticleCreate) -> Optional[Article]:
        """
        Create a new article.

        Args:
            article_data: Article data to create

        Returns:
            Created article or None if failed
        """
        try:
            # Check if article with same URL already exists
            existing = self.get_article_by_url(article_data.url)
            if existing:
                logger.warning(f"Article with URL already exists: {article_data.url}")
                return existing

            # Create new article
            db_article = Article(**article_data.dict())
            self.db.add(db_article)
            self.db.commit()
            self.db.refresh(db_article)

            logger.info(
                f"Created article: {db_article.id} - {db_article.title[:50]}..."
            )
            return db_article

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating article: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating article: {str(e)}")
            return None

    def get_article(self, article_id: int) -> Optional[Article]:
        """
        Get article by ID.

        Args:
            article_id: Article ID

        Returns:
            Article or None if not found
        """
        return self.db.query(Article).filter(Article.id == article_id).first()

    def get_article_by_url(self, url: str) -> Optional[Article]:
        """
        Get article by URL.

        Args:
            url: Article URL

        Returns:
            Article or None if not found
        """
        return self.db.query(Article).filter(Article.url == url).first()

    def get_articles(
        self,
        skip: int = 0,
        limit: int = 100,
        source: Optional[str] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_credibility: Optional[float] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Article], int]:
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

        Returns:
            Tuple of (articles list, total count)
        """
        query = self.db.query(Article)

        # Apply filters
        filters = []

        if source:
            filters.append(Article.source.ilike(f"%{source}%"))

        if category:
            filters.append(Article.category.ilike(f"%{category}%"))

        if author:
            filters.append(Article.author.ilike(f"%{author}%"))

        if date_from:
            filters.append(Article.published_at >= date_from)

        if date_to:
            filters.append(Article.published_at <= date_to)

        if min_credibility is not None:
            filters.append(Article.credibility_score >= min_credibility)

        if filters:
            query = query.filter(and_(*filters))

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting
        sort_column = getattr(Article, sort_by, Article.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        articles = query.offset(skip).limit(limit).all()

        return articles, total_count

    def search_articles(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        search_fields: List[str] = None,
        **filters,
    ) -> Tuple[List[Article], int]:
        """
        Search articles by text query.

        Args:
            query: Search query
            skip: Number of articles to skip
            limit: Maximum number of articles to return
            search_fields: Fields to search in (title, content, summary)
            **filters: Additional filters

        Returns:
            Tuple of (articles list, total count)
        """
        if not query.strip():
            return self.get_articles(skip=skip, limit=limit, **filters)

        # Default search fields
        if search_fields is None:
            search_fields = ["title", "content", "summary"]

        db_query = self.db.query(Article)

        # Build search conditions
        search_conditions = []
        search_term = f"%{query}%"

        if "title" in search_fields:
            search_conditions.append(Article.title.ilike(search_term))

        if "content" in search_fields:
            search_conditions.append(Article.content.ilike(search_term))

        if "summary" in search_fields and Article.summary is not None:
            search_conditions.append(Article.summary.ilike(search_term))

        if "author" in search_fields and Article.author is not None:
            search_conditions.append(Article.author.ilike(search_term))

        if "tags" in search_fields and Article.tags is not None:
            search_conditions.append(Article.tags.ilike(search_term))

        # Apply search conditions
        if search_conditions:
            db_query = db_query.filter(or_(*search_conditions))

        # Apply additional filters
        filter_conditions = []

        if filters.get("source"):
            filter_conditions.append(Article.source.ilike(f"%{filters['source']}%"))

        if filters.get("category"):
            filter_conditions.append(Article.category.ilike(f"%{filters['category']}%"))

        if filters.get("min_credibility") is not None:
            filter_conditions.append(
                Article.credibility_score >= filters["min_credibility"]
            )

        if filter_conditions:
            db_query = db_query.filter(and_(*filter_conditions))

        # Get total count
        total_count = db_query.count()

        # Apply ordering (relevance-based)
        # For now, order by credibility score and created date
        db_query = db_query.order_by(
            desc(Article.credibility_score), desc(Article.created_at)
        )

        # Apply pagination
        articles = db_query.offset(skip).limit(limit).all()

        return articles, total_count

    def update_article(
        self, article_id: int, article_data: ArticleUpdate
    ) -> Optional[Article]:
        """
        Update an article.

        Args:
            article_id: Article ID
            article_data: Updated article data

        Returns:
            Updated article or None if not found
        """
        try:
            article = self.get_article(article_id)
            if not article:
                return None

            # Update fields
            update_data = article_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(article, field, value)

            # Update timestamp
            article.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(article)

            logger.info(f"Updated article: {article.id}")
            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating article {article_id}: {str(e)}")
            return None

    def delete_article(self, article_id: int) -> bool:
        """
        Delete an article.

        Args:
            article_id: Article ID

        Returns:
            True if deleted, False if not found
        """
        try:
            article = self.get_article(article_id)
            if not article:
                return False

            self.db.delete(article)
            self.db.commit()

            logger.info(f"Deleted article: {article_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting article {article_id}: {str(e)}")
            return False

    def bulk_create_articles(
        self, articles_data: List[ArticleCreate]
    ) -> Tuple[List[Article], List[str]]:
        """
        Create multiple articles in bulk.

        Args:
            articles_data: List of article data

        Returns:
            Tuple of (created articles, list of errors)
        """
        created_articles = []
        errors = []

        for article_data in articles_data:
            try:
                article = self.create_article(article_data)
                if article:
                    created_articles.append(article)
                else:
                    errors.append(
                        f"Failed to create article: {article_data.title[:50]}..."
                    )
            except Exception as e:
                errors.append(
                    f"Error creating article {article_data.title[:50]}...: {str(e)}"
                )

        return created_articles, errors

    def get_article_statistics(self) -> Dict[str, Any]:
        """
        Get article statistics.

        Returns:
            Dictionary containing various statistics
        """
        try:
            # Basic counts
            total_articles = self.db.query(Article).count()

            # Articles by source
            sources = (
                self.db.query(Article.source, func.count(Article.id).label("count"))
                .group_by(Article.source)
                .all()
            )

            # Articles by category
            categories = (
                self.db.query(Article.category, func.count(Article.id).label("count"))
                .filter(Article.category.isnot(None))
                .group_by(Article.category)
                .all()
            )

            # Recent articles (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_articles = (
                self.db.query(Article).filter(Article.created_at >= week_ago).count()
            )

            # Average credibility score
            avg_credibility = (
                self.db.query(func.avg(Article.credibility_score))
                .filter(Article.credibility_score.isnot(None))
                .scalar()
            )

            # Articles with high credibility (>= 8.0)
            high_credibility = (
                self.db.query(Article).filter(Article.credibility_score >= 8.0).count()
            )

            return {
                "total_articles": total_articles,
                "recent_articles": recent_articles,
                "average_credibility": round(avg_credibility or 0, 2),
                "high_credibility_articles": high_credibility,
                "sources": [{"source": s.source, "count": s.count} for s in sources],
                "categories": [
                    {"category": c.category, "count": c.count} for c in categories
                ],
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting article statistics: {str(e)}")
            return {
                "error": str(e),
                "total_articles": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

    def get_similar_articles(self, article_id: int, limit: int = 5) -> List[Article]:
        """
        Get articles similar to the given article.

        Args:
            article_id: Article ID to find similar articles for
            limit: Maximum number of similar articles to return

        Returns:
            List of similar articles
        """
        article = self.get_article(article_id)
        if not article:
            return []

        # Simple similarity based on category and source
        query = self.db.query(Article).filter(Article.id != article_id)

        # Prefer same category
        if article.category:
            query = query.filter(Article.category == article.category)

        # Then same source
        similar_articles = (
            query.filter(Article.source == article.source)
            .order_by(desc(Article.credibility_score))
            .limit(limit)
            .all()
        )

        # If not enough, get from same category but different source
        if len(similar_articles) < limit and article.category:
            remaining = limit - len(similar_articles)
            additional = (
                self.db.query(Article)
                .filter(
                    and_(
                        Article.id != article_id,
                        Article.category == article.category,
                        Article.source != article.source,
                        Article.id.notin_([a.id for a in similar_articles]),
                    )
                )
                .order_by(desc(Article.credibility_score))
                .limit(remaining)
                .all()
            )

            similar_articles.extend(additional)

        return similar_articles
