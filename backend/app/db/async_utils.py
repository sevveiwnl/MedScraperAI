"""Async database utility functions."""

from typing import Dict, List, Any, Optional
from datetime import datetime

from app.db.async_session import async_db


class AsyncDatabaseUtils:
    """Utility class for async database operations."""

    @staticmethod
    async def check_table_exists(table_name: str) -> bool:
        """Check if a table exists in the database."""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        )
        """
        result = await async_db.execute_one(query, table_name)
        return result[0] if result else False

    @staticmethod
    async def get_table_count(table_name: str) -> int:
        """Get the count of records in a table."""
        try:
            # Note: This is potentially unsafe for SQL injection in production
            # In real apps, you'd want to validate table_name or use a whitelist
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = await async_db.execute_one(query)
            return result[0] if result else 0
        except Exception:
            return 0

    @staticmethod
    async def get_database_info() -> Dict[str, Any]:
        """Get basic database information."""
        try:
            # Get PostgreSQL version
            version_result = await async_db.execute_one("SELECT version()")
            version = version_result[0] if version_result else "Unknown"

            # Get current timestamp
            time_result = await async_db.execute_one("SELECT NOW()")
            current_time = time_result[0] if time_result else None

            # Get database name
            db_name_result = await async_db.execute_one("SELECT current_database()")
            db_name = db_name_result[0] if db_name_result else "Unknown"

            # Check if articles table exists
            articles_exists = await AsyncDatabaseUtils.check_table_exists("articles")

            return {
                "database_name": db_name,
                "version": version,
                "current_time": current_time.isoformat() if current_time else None,
                "articles_table_exists": articles_exists,
                "articles_count": (
                    await AsyncDatabaseUtils.get_table_count("articles")
                    if articles_exists
                    else 0
                ),
            }
        except Exception as e:
            return {"error": f"Failed to get database info: {str(e)}"}

    @staticmethod
    async def execute_health_queries() -> List[Dict[str, Any]]:
        """Execute a set of health check queries."""
        queries = [
            ("basic_select", "SELECT 1 as test"),
            ("timestamp_check", "SELECT NOW() as current_time"),
            (
                "connection_count",
                "SELECT count(*) as active_connections FROM pg_stat_activity",
            ),
        ]

        results = []
        for name, query in queries:
            try:
                start_time = datetime.utcnow()
                result = await async_db.execute_one(query)
                end_time = datetime.utcnow()

                results.append(
                    {
                        "query_name": name,
                        "status": "success",
                        "result": dict(result) if result else None,
                        "execution_time_ms": (end_time - start_time).total_seconds()
                        * 1000,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "query_name": name,
                        "status": "error",
                        "error": str(e),
                        "execution_time_ms": None,
                    }
                )

        return results


# Create utility instance
async_db_utils = AsyncDatabaseUtils()
