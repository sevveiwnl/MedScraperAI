"""Celery worker entry point for MedScraperAI."""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Run the Celery worker
    celery_app.start()
