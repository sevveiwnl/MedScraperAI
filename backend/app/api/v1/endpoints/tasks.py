"""Task management and monitoring endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.tasks.ping import simple_ping, slow_ping, random_ping, health_check_task


router = APIRouter()


class TaskResponse(BaseModel):
    """Response model for task operations."""

    task_id: str
    status: str
    message: str


class TaskResult(BaseModel):
    """Model for task result data."""

    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/ping", response_model=TaskResponse)
async def trigger_ping_task():
    """
    Trigger a simple ping task to test Celery connectivity.

    Returns:
        TaskResponse with task ID and status
    """
    try:
        task = simple_ping.delay()
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message="Ping task submitted successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit ping task: {str(e)}"
        )


@router.post("/ping/slow", response_model=TaskResponse)
async def trigger_slow_ping_task(delay: int = 5):
    """
    Trigger a slow ping task with specified delay.

    Args:
        delay: Number of seconds to delay (default: 5)

    Returns:
        TaskResponse with task ID and status
    """
    if delay < 1 or delay > 60:
        raise HTTPException(
            status_code=400, detail="Delay must be between 1 and 60 seconds"
        )

    try:
        task = slow_ping.delay(delay)
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message=f"Slow ping task submitted with {delay}s delay",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit slow ping task: {str(e)}"
        )


@router.post("/ping/random", response_model=TaskResponse)
async def trigger_random_ping_task(min_delay: int = 1, max_delay: int = 10):
    """
    Trigger a random ping task with variable delay.

    Args:
        min_delay: Minimum delay in seconds (default: 1)
        max_delay: Maximum delay in seconds (default: 10)

    Returns:
        TaskResponse with task ID and status
    """
    if min_delay < 1 or max_delay > 60 or min_delay >= max_delay:
        raise HTTPException(status_code=400, detail="Invalid delay parameters")

    try:
        task = random_ping.delay(min_delay, max_delay)
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message=f"Random ping task submitted with delay range {min_delay}-{max_delay}s",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit random ping task: {str(e)}"
        )


@router.post("/health-check", response_model=TaskResponse)
async def trigger_health_check_task():
    """
    Trigger a health check task to monitor worker status.

    Returns:
        TaskResponse with task ID and status
    """
    try:
        task = health_check_task.delay()
        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message="Health check task submitted successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit health check task: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskResult)
async def get_task_status(task_id: str):
    """
    Get the status and result of a specific task.

    Args:
        task_id: The ID of the task to check

    Returns:
        TaskResult with current task status and result
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = TaskResult(
            task_id=task_id,
            status=task_result.status,
        )

        if task_result.successful():
            response.result = task_result.result
        elif task_result.failed():
            response.error = str(task_result.info)
        elif task_result.status == "PROGRESS":
            response.meta = task_result.info

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running task.

    Args:
        task_id: The ID of the task to cancel

    Returns:
        Dict with cancellation status
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {
            "message": f"Task {task_id} cancellation requested",
            "task_id": task_id,
            "status": "cancellation_requested",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/workers")
async def get_worker_status():
    """
    Get the status of all Celery workers.

    Returns:
        Dict containing worker information
    """
    try:
        # Get active workers
        inspect = celery_app.control.inspect()

        # Gather worker information
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        worker_stats = inspect.stats()

        return {
            "workers": {
                "active": active_workers or {},
                "registered_tasks": registered_tasks or {},
                "stats": worker_stats or {},
            },
            "total_workers": len(active_workers) if active_workers else 0,
            "broker_url": celery_app.conf.broker_url,
            "backend_url": celery_app.conf.result_backend,
        }
    except Exception as e:
        return {
            "error": f"Failed to get worker status: {str(e)}",
            "workers": {},
            "total_workers": 0,
        }
