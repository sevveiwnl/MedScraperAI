"""Celery application configuration for MedScraperAI."""

from celery import Celery

from app.core.config import settings


# Create Celery instance
celery_app = Celery(
    "medscraper",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ping",
        "app.tasks.scraper",
        "app.tasks.nlp",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.ping.*": {"queue": "ping"},
        "app.tasks.scraper.*": {"queue": "scraper"},
        "app.tasks.nlp.*": {"queue": "nlp"},
    },
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_compression="gzip",
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat schedule (for periodic tasks)
    beat_schedule={
        # Scheduled scraping every 4 hours
        "scheduled-scrape": {
            "task": "scraper.scheduled_scrape",
            "schedule": 4 * 60 * 60,  # 4 hours in seconds
            "options": {"queue": "scraper"},
        },
        # Scheduled scrape and summarize every 6 hours
        "scheduled-scrape-and-summarize": {
            "task": "scraper.scheduled_scrape_and_summarize",
            "schedule": 6 * 60 * 60,  # 6 hours in seconds
            "options": {"queue": "scraper"},
        },
        # Daily ping task for monitoring
        "daily-ping": {
            "task": "ping.ping_task",
            "schedule": 24 * 60 * 60,  # 24 hours in seconds
            "options": {"queue": "ping"},
        },
    },
)


# Autodiscover tasks
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f"Request: {self.request!r}")
    return {"message": "Debug task executed successfully"}
