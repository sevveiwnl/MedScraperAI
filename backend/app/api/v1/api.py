"""Main API router for v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, tasks, scraper, articles


api_router = APIRouter()

# Include health check endpoint
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Include task management endpoints
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Include scraper endpoints
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])

# Include article endpoints
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
