"""Database configuration and setup for MedScraperAI."""

from .base import Base
from .session import SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
