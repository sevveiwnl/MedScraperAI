"""Health check endpoints."""

import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings


router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint.

    Checks:
    - API status
    - Database connectivity
    - System timestamp
    - Configuration status

    Returns:
        Dict containing health status information
    """
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "checks": {},
    }

    # Database connectivity check
    try:
        # Simple database query to test connectivity
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }

    # System check
    health_status["checks"]["system"] = {
        "status": "healthy",
        "message": "System operational",
        "uptime": "N/A",  # Will be implemented with proper metrics later
    }

    # Configuration check
    health_status["checks"]["configuration"] = {
        "status": "healthy",
        "message": "Configuration loaded successfully",
        "api_version": settings.API_V1_STR,
    }

    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)
    health_status["response_time_ms"] = response_time

    # Set appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for basic availability checking.

    Returns:
        Simple pong response
    """
    return {
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint for container orchestration.

    Returns 200 if service is ready to handle requests,
    503 if service is not ready.

    Args:
        db: Database session dependency

    Returns:
        Readiness status
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Service is ready to handle requests",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Service is not ready: {str(e)}",
            },
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint for container orchestration.

    Returns 200 if service is alive, regardless of dependencies.

    Returns:
        Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Service is alive",
    }
