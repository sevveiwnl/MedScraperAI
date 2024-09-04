"""Background tasks for MedScraperAI."""

# Import all task modules to ensure they're registered with Celery
from . import ping, scraper, nlp

__all__ = ["ping", "scraper", "nlp"]
