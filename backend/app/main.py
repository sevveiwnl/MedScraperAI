"""Main FastAPI application for MedScraperAI."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.async_session import async_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 MedScraperAI is starting up...")

    # Initialize async database connection pool
    try:
        await async_db.connect()
        print("✅ Async database connection pool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize async database: {e}")
        # Don't raise - let the app start anyway for debugging

    yield

    # Shutdown
    print("🔥 MedScraperAI is shutting down...")

    # Close async database connection pool
    try:
        await async_db.disconnect()
        print("✅ Async database connection pool closed")
    except Exception as e:
        print(f"❌ Error closing async database: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Advanced medical data scraping and research platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": "Welcome to MedScraperAI API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("DEBUG", "false").lower() == "true" else False,
    )
