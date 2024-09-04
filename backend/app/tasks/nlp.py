"""NLP tasks for natural language processing functionality."""

from datetime import datetime
from typing import Dict, Any

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="nlp.placeholder")
def placeholder_nlp_task(self) -> Dict[str, Any]:
    """
    Placeholder NLP task.

    This will be implemented in future commits.

    Returns:
        Dict containing placeholder response
    """
    return {
        "message": "NLP tasks will be implemented soon",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": self.request.id,
        "status": "placeholder",
    }
