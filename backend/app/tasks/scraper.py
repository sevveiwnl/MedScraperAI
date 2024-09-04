"""Scraper tasks for web scraping functionality."""

from datetime import datetime
from typing import Dict, Any

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="scraper.placeholder")
def placeholder_scraper_task(self) -> Dict[str, Any]:
    """
    Placeholder scraper task.

    This will be implemented in future commits.

    Returns:
        Dict containing placeholder response
    """
    return {
        "message": "Scraper tasks will be implemented soon",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": self.request.id,
        "status": "placeholder",
    }
