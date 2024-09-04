"""Ping tasks for testing Celery functionality."""

import time
import random
from datetime import datetime
from typing import Dict, Any

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="ping.simple_ping")
def simple_ping(self) -> Dict[str, Any]:
    """
    Simple ping task for testing Celery connectivity.

    Returns:
        Dict containing ping response with timestamp and task info
    """
    return {
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": self.request.id,
        "worker": self.request.hostname,
        "queue": getattr(self.request, "delivery_info", {}).get(
            "routing_key", "unknown"
        ),
    }


@celery_app.task(bind=True, name="ping.slow_ping")
def slow_ping(self, delay: int = 5) -> Dict[str, Any]:
    """
    Slow ping task for testing task execution and monitoring.

    Args:
        delay: Number of seconds to sleep (default: 5)

    Returns:
        Dict containing ping response with execution time
    """
    start_time = time.time()

    # Update task state to indicate progress
    self.update_state(
        state="PROGRESS",
        meta={
            "current": 0,
            "total": delay,
            "status": f"Sleeping for {delay} seconds...",
        },
    )

    # Simulate work with progress updates
    for i in range(delay):
        time.sleep(1)
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1,
                "total": delay,
                "status": f"Completed {i + 1}/{delay} seconds",
            },
        )

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)

    return {
        "message": "slow pong",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": self.request.id,
        "worker": self.request.hostname,
        "delay_requested": delay,
        "execution_time": execution_time,
        "status": "completed",
    }


@celery_app.task(bind=True, name="ping.random_ping")
def random_ping(self, min_delay: int = 1, max_delay: int = 10) -> Dict[str, Any]:
    """
    Random ping task with variable execution time.

    Args:
        min_delay: Minimum delay in seconds (default: 1)
        max_delay: Maximum delay in seconds (default: 10)

    Returns:
        Dict containing ping response with random execution details
    """
    delay = random.randint(min_delay, max_delay)
    start_time = time.time()

    # Random task behavior
    behaviors = ["normal", "slow", "fast"]
    behavior = random.choice(behaviors)

    if behavior == "slow":
        # Simulate slow processing
        time.sleep(delay)
    elif behavior == "fast":
        # Simulate fast processing
        time.sleep(delay * 0.1)
    else:
        # Normal processing
        time.sleep(delay * 0.5)

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)

    return {
        "message": "random pong",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": self.request.id,
        "worker": self.request.hostname,
        "behavior": behavior,
        "planned_delay": delay,
        "actual_execution_time": execution_time,
        "randomness": random.random(),
    }


@celery_app.task(bind=True, name="ping.health_check")
def health_check_task(self) -> Dict[str, Any]:
    """
    Health check task for monitoring Celery worker status.

    Returns:
        Dict containing health status and system information
    """
    import psutil
    import os

    try:
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get process information
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": round(disk.free / (1024**3), 2),
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "pid": os.getpid(),
                "ppid": os.getppid(),
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "error": str(e),
        }
