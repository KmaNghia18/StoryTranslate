"""
Task store for tracking async image translation progress.
Uses simple polling with in-memory dict. Thread-safe.
"""

import uuid
import threading
from dataclasses import dataclass, field
from enum import Enum


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


# In-memory task store (thread-safe via lock)
_tasks: dict[str, TaskInfo] = {}
_lock = threading.Lock()
_cleanup_threshold = 50


def create_task() -> str:
    """Create a new task and return its ID."""
    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = TaskInfo(task_id=task_id)
        # Clean up old completed tasks if too many
        if len(_tasks) > _cleanup_threshold:
            _cleanup_old_tasks()
    return task_id


def get_task(task_id: str) -> TaskInfo | None:
    """Get task info by ID."""
    return _tasks.get(task_id)


def update_task(task_id: str, progress: int, step: str, status: TaskStatus = TaskStatus.PROCESSING):
    """Update task progress. Thread-safe."""
    task = _tasks.get(task_id)
    if task:
        task.progress = progress
        task.step = step
        task.status = status


def complete_task(task_id: str, result: bytes, detections: list[dict]):
    """Mark task as completed with results."""
    task = _tasks.get(task_id)
    if task:
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.step = "Hoàn thành!"
        task.result = result
        task.detections = detections


def fail_task(task_id: str, error: str):
    """Mark task as failed."""
    task = _tasks.get(task_id)
    if task:
        task.status = TaskStatus.FAILED
        task.error = error


def _cleanup_old_tasks():
    """Remove completed/failed tasks to free memory."""
    to_remove = []
    for tid, task in _tasks.items():
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            to_remove.append(tid)
    for tid in to_remove[:len(to_remove) - 5]:
        del _tasks[tid]
