"""Main API router for v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, tasks


api_router = APIRouter()

# Include health check endpoint
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Include task management endpoints
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
