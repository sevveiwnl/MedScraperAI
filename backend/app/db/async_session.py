"""Async PostgreSQL connection pool using asyncpg."""

import asyncio
import asyncpg
from typing import Optional
from contextlib import asynccontextmanager

from app.core.config import settings


class AsyncDatabase:
    """Async PostgreSQL database manager."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Create async connection pool."""
        if self.pool is not None:
            return

        async with self._lock:
            if self.pool is not None:
                return

            # Parse database URL for asyncpg
            db_url = settings.DATABASE_URL
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgres://", 1)

            try:
                self.pool = await asyncpg.create_pool(
                    db_url,
                    min_size=5,  # Minimum connections in pool
                    max_size=20,  # Maximum connections in pool
                    max_queries=50000,  # Max queries per connection
                    max_inactive_connection_lifetime=300,  # 5 minutes
                    command_timeout=60,  # 60 seconds timeout for commands
                )
                print("✅ Async PostgreSQL connection pool created successfully")
            except Exception as e:
                print(f"❌ Failed to create async connection pool: {e}")
                raise

    async def disconnect(self) -> None:
        """Close async connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            print("🔌 Async PostgreSQL connection pool closed")

    async def get_connection(self):
        """Get connection from pool."""
        if self.pool is None:
            await self.connect()
        return self.pool.acquire()

    @asynccontextmanager
    async def connection(self):
        """Context manager for database connections."""
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            yield conn

    async def execute_query(self, query: str, *args):
        """Execute a query and return results."""
        async with self.connection() as conn:
            return await conn.fetch(query, *args)

    async def execute_one(self, query: str, *args):
        """Execute a query and return single result."""
        async with self.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        """Execute a query without returning results."""
        async with self.connection() as conn:
            return await conn.execute(query, *args)

    async def health_check(self) -> dict:
        """Check database health."""
        try:
            start_time = asyncio.get_event_loop().time()

            async with self.connection() as conn:
                result = await conn.fetchval("SELECT 1")

            end_time = asyncio.get_event_loop().time()
            response_time = round((end_time - start_time) * 1000, 2)

            return {
                "status": "healthy",
                "message": "Async database connection successful",
                "response_time_ms": response_time,
                "pool_size": self.pool.get_size() if self.pool else 0,
                "pool_free": len(self.pool._queue._queue) if self.pool else 0,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Async database connection failed: {str(e)}",
                "response_time_ms": None,
                "pool_size": 0,
                "pool_free": 0,
            }


# Global async database instance
async_db = AsyncDatabase()


async def get_async_db():
    """Dependency to get async database connection."""
    async with async_db.connection() as conn:
        yield conn
