"""NLP tasks for natural language processing functionality."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.celery_app import celery_app
from app.services.summarizer_service import SummarizerService, SummarizerType


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="nlp.summarize_text")
def summarize_text_task(
    self,
    text: str,
    max_length: int = 200,
    min_length: int = 50,
    style: str = "professional",
    focus: str = "medical",
    summarizer_type: str = "openai",
) -> Dict[str, Any]:
    """
    Summarize text using the specified summarizer.

    Args:
        text: Text to summarize
        max_length: Maximum summary length in words
        min_length: Minimum summary length in words
        style: Summary style
        focus: Summary focus
        summarizer_type: Type of summarizer to use

    Returns:
        Dictionary containing summarization result
    """
    logger.info(f"Starting text summarization task")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": "Starting text summarization",
            "text_length": len(text),
            "summarizer_type": summarizer_type,
        },
    )

    try:
        # Create summarizer service
        summarizer = SummarizerService(SummarizerType(summarizer_type))

        # Generate summary
        result = summarizer.summarize_text(
            text=text,
            max_length=max_length,
            min_length=min_length,
            style=style,
            focus=focus,
        )

        # Update task state
        if result["success"]:
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "Text summarization completed",
                    "summary_length": (
                        len(result["summary"]) if result["summary"] else 0
                    ),
                    "summarizer_type": summarizer_type,
                },
            )
        else:
            self.update_state(
                state="FAILURE",
                meta={
                    "status": f"Text summarization failed: {result['error']}",
                    "summarizer_type": summarizer_type,
                },
            )

        # Add task metadata
        result["task_id"] = self.request.id
        result["timestamp"] = datetime.utcnow().isoformat()

        logger.info(f"Text summarization task completed: {result['success']}")
        return result

    except Exception as e:
        error_msg = f"Text summarization task failed: {str(e)}"
        logger.error(error_msg)

        self.update_state(
            state="FAILURE",
            meta={
                "status": error_msg,
                "summarizer_type": summarizer_type,
            },
        )

        return {
            "success": False,
            "error": error_msg,
            "summary": None,
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="nlp.summarize_article")
def summarize_article_task(
    self,
    title: str,
    content: str,
    author: Optional[str] = None,
    source: Optional[str] = None,
    max_length: int = 150,
    min_length: int = 50,
    style: str = "professional",
    focus: str = "medical",
    summarizer_type: str = "openai",
) -> Dict[str, Any]:
    """
    Summarize an article using the specified summarizer.

    Args:
        title: Article title
        content: Article content
        author: Article author (optional)
        source: Article source (optional)
        max_length: Maximum summary length in words
        min_length: Minimum summary length in words
        style: Summary style
        focus: Summary focus
        summarizer_type: Type of summarizer to use

    Returns:
        Dictionary containing summarization result
    """
    logger.info(f"Starting article summarization task: {title[:50]}...")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Starting article summarization: {title[:50]}...",
            "title": title,
            "content_length": len(content),
            "summarizer_type": summarizer_type,
        },
    )

    try:
        # Create summarizer service
        summarizer = SummarizerService(SummarizerType(summarizer_type))

        # Generate summary
        result = summarizer.summarize_article(
            title=title,
            content=content,
            author=author,
            source=source,
            max_length=max_length,
            min_length=min_length,
            style=style,
            focus=focus,
        )

        # Update task state
        if result["success"]:
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": f"Article summarization completed: {title[:50]}...",
                    "title": title,
                    "summary_length": (
                        len(result["summary"]) if result["summary"] else 0
                    ),
                    "summarizer_type": summarizer_type,
                },
            )
        else:
            self.update_state(
                state="FAILURE",
                meta={
                    "status": f"Article summarization failed: {result['error']}",
                    "title": title,
                    "summarizer_type": summarizer_type,
                },
            )

        # Add task metadata
        result["task_id"] = self.request.id
        result["timestamp"] = datetime.utcnow().isoformat()

        logger.info(f"Article summarization task completed: {result['success']}")
        return result

    except Exception as e:
        error_msg = f"Article summarization task failed: {str(e)}"
        logger.error(error_msg)

        self.update_state(
            state="FAILURE",
            meta={
                "status": error_msg,
                "title": title,
                "summarizer_type": summarizer_type,
            },
        )

        return {
            "success": False,
            "error": error_msg,
            "summary": None,
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="nlp.batch_summarize")
def batch_summarize_task(
    self,
    texts: List[str],
    max_length: int = 200,
    min_length: int = 50,
    style: str = "professional",
    focus: str = "medical",
    summarizer_type: str = "openai",
) -> Dict[str, Any]:
    """
    Batch summarize multiple texts using the specified summarizer.

    Args:
        texts: List of texts to summarize
        max_length: Maximum summary length in words
        min_length: Minimum summary length in words
        style: Summary style
        focus: Summary focus
        summarizer_type: Type of summarizer to use

    Returns:
        Dictionary containing batch summarization results
    """
    logger.info(f"Starting batch summarization task: {len(texts)} texts")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Starting batch summarization: {len(texts)} texts",
            "total_texts": len(texts),
            "current_text": 0,
            "summarizer_type": summarizer_type,
        },
    )

    try:
        # Create summarizer service
        summarizer = SummarizerService(SummarizerType(summarizer_type))

        # Generate summaries
        results = []
        for i, text in enumerate(texts, 1):
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Summarizing text {i}/{len(texts)}",
                    "total_texts": len(texts),
                    "current_text": i,
                    "summarizer_type": summarizer_type,
                },
            )

            # Summarize individual text
            result = summarizer.summarize_text(
                text=text,
                max_length=max_length,
                min_length=min_length,
                style=style,
                focus=focus,
            )

            # Add batch metadata
            result["batch_index"] = i - 1
            result["batch_total"] = len(texts)
            results.append(result)

        # Calculate stats
        success_count = sum(1 for r in results if r["success"])
        error_count = len(results) - success_count

        # Update task state
        self.update_state(
            state="SUCCESS",
            meta={
                "status": f"Batch summarization completed: {success_count}/{len(texts)} successful",
                "total_texts": len(texts),
                "success_count": success_count,
                "error_count": error_count,
                "summarizer_type": summarizer_type,
            },
        )

        batch_result = {
            "success": True,
            "results": results,
            "total_count": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / len(results) if results else 0,
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Batch summarization task completed: {success_count}/{len(texts)} successful"
        )
        return batch_result

    except Exception as e:
        error_msg = f"Batch summarization task failed: {str(e)}"
        logger.error(error_msg)

        self.update_state(
            state="FAILURE",
            meta={
                "status": error_msg,
                "total_texts": len(texts),
                "summarizer_type": summarizer_type,
            },
        )

        return {
            "success": False,
            "error": error_msg,
            "results": [],
            "total_count": len(texts),
            "success_count": 0,
            "error_count": len(texts),
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="nlp.summarize_article_by_id")
def summarize_article_by_id_task(
    self,
    article_id: int,
    max_length: int = 150,
    min_length: int = 50,
    style: str = "professional",
    focus: str = "medical",
    summarizer_type: str = "openai",
    save_to_db: bool = True,
) -> Dict[str, Any]:
    """
    Summarize an article by ID and optionally save the summary to the database.

    Args:
        article_id: ID of the article to summarize
        max_length: Maximum summary length in words
        min_length: Minimum summary length in words
        style: Summary style
        focus: Summary focus
        summarizer_type: Type of summarizer to use
        save_to_db: Whether to save the summary to the database

    Returns:
        Dictionary containing summarization result
    """
    logger.info(f"Starting article summarization by ID task: {article_id}")

    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Starting article summarization for ID: {article_id}",
            "article_id": article_id,
            "summarizer_type": summarizer_type,
        },
    )

    try:
        # Import here to avoid circular imports
        from app.services.article_service import ArticleService
        from app.db.session import get_db

        # Get article from database
        db_session = next(get_db())
        article_service = ArticleService(db_session)

        article = article_service.get_article(article_id)
        if not article:
            error_msg = f"Article with ID {article_id} not found"
            logger.error(error_msg)

            self.update_state(
                state="FAILURE",
                meta={
                    "status": error_msg,
                    "article_id": article_id,
                },
            )

            return {
                "success": False,
                "error": error_msg,
                "summary": None,
                "article_id": article_id,
                "task_id": self.request.id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Create summarizer service
        summarizer = SummarizerService(SummarizerType(summarizer_type))

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

        # Save summary to database if requested and successful
        if save_to_db and result["success"]:
            try:
                from app.schemas.article import ArticleUpdate

                # Update article with generated summary
                article_update = ArticleUpdate(summary=result["summary"])
                updated_article = article_service.update_article(
                    article_id, article_update
                )

                if updated_article:
                    result["metadata"]["saved_to_db"] = True
                    result["metadata"]["updated_article_id"] = article_id
                    logger.info(f"Summary saved to database for article {article_id}")
                else:
                    logger.warning(
                        f"Failed to save summary to database for article {article_id}"
                    )
                    result["metadata"]["saved_to_db"] = False

            except Exception as e:
                logger.error(f"Error saving summary to database: {str(e)}")
                result["metadata"]["saved_to_db"] = False
                result["metadata"]["save_error"] = str(e)

        # Update task state
        if result["success"]:
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": f"Article summarization completed for ID: {article_id}",
                    "article_id": article_id,
                    "title": article.title,
                    "summary_length": (
                        len(result["summary"]) if result["summary"] else 0
                    ),
                    "summarizer_type": summarizer_type,
                },
            )
        else:
            self.update_state(
                state="FAILURE",
                meta={
                    "status": f"Article summarization failed for ID: {article_id}",
                    "article_id": article_id,
                    "error": result["error"],
                    "summarizer_type": summarizer_type,
                },
            )

        # Add task metadata
        result["article_id"] = article_id
        result["task_id"] = self.request.id
        result["timestamp"] = datetime.utcnow().isoformat()

        db_session.close()

        logger.info(f"Article summarization by ID task completed: {result['success']}")
        return result

    except Exception as e:
        error_msg = f"Article summarization by ID task failed: {str(e)}"
        logger.error(error_msg)

        self.update_state(
            state="FAILURE",
            meta={
                "status": error_msg,
                "article_id": article_id,
                "summarizer_type": summarizer_type,
            },
        )

        return {
            "success": False,
            "error": error_msg,
            "summary": None,
            "article_id": article_id,
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="nlp.placeholder")
def placeholder_nlp_task(self) -> Dict[str, Any]:
    """
    Placeholder NLP task for future functionality.

    Returns:
        Dict containing placeholder response
    """
    return {
        "message": "Additional NLP tasks will be implemented in future commits",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": self.request.id,
        "status": "placeholder",
    }
