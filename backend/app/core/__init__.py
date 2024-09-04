"""Core configuration and utilities for MedScraperAI."""

from .celery_app import celery_app
from .config import settings

__all__ = ["celery_app", "settings"]
