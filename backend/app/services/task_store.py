"""
Task store for tracking async image translation progress.
Uses in-memory dict - suitable for single-server deployment.
"""

import uuid
import asyncio
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInfo:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0  # 0-100
    step: str = ""
    result: bytes | None = None
    detections: list[dict] = field(default_factory=list)
    error: str | None = None
    _event: asyncio.Event = field(default_factory=lambda: asyncio.Event())
    _progress_events: list[asyncio.Event] = field(default_factory=list)


# In-memory task store
_tasks: dict[str, TaskInfo] = {}
_cleanup_threshold = 50  # Clean up old tasks when this many accumulate


def create_task() -> str:
    """Create a new task and return its ID."""
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = TaskInfo(task_id=task_id)
    
    # Clean up old completed tasks if too many
    if len(_tasks) > _cleanup_threshold:
        _cleanup_old_tasks()
    
    return task_id


def get_task(task_id: str) -> TaskInfo | None:
    """Get task info by ID."""
    return _tasks.get(task_id)


def update_task(task_id: str, progress: int, step: str, status: TaskStatus = TaskStatus.PROCESSING):
    """Update task progress."""
    task = _tasks.get(task_id)
    if task:
        task.progress = progress
        task.step = step
        task.status = status
        # Signal any waiting coroutines
        for event in task._progress_events:
            event.set()
        task._progress_events.clear()


def complete_task(task_id: str, result: bytes, detections: list[dict]):
    """Mark task as completed with results."""
    task = _tasks.get(task_id)
    if task:
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.step = "Hoàn thành!"
        task.result = result
        task.detections = detections
        task._event.set()
        for event in task._progress_events:
            event.set()
        task._progress_events.clear()


def fail_task(task_id: str, error: str):
    """Mark task as failed."""
    task = _tasks.get(task_id)
    if task:
        task.status = TaskStatus.FAILED
        task.error = error
        task._event.set()
        for event in task._progress_events:
            event.set()
        task._progress_events.clear()


async def wait_for_progress(task_id: str, timeout: float = 30.0) -> TaskInfo | None:
    """Wait for task progress update (async)."""
    task = _tasks.get(task_id)
    if not task:
        return None
    
    event = asyncio.Event()
    task._progress_events.append(event)
    
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    
    return task


def _cleanup_old_tasks():
    """Remove completed/failed tasks to free memory."""
    to_remove = []
    for tid, task in _tasks.items():
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            to_remove.append(tid)
    
    for tid in to_remove[:len(to_remove) - 5]:  # Keep last 5
        del _tasks[tid]
