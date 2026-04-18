"""
Async task processing for Biomech AI - Phase 2.6 Performance Optimization

Implements background task queue for long-running operations with status tracking,
retry logic, and failure handling.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
import uuid
import os

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task:
    """Represents an async task"""
    
    def __init__(self, task_id: str, operation: str, data: Dict[str, Any], priority: int = 5):
        self.task_id = task_id
        self.operation = operation
        self.data = data
        self.priority = priority  # 1-10, higher = more important
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        self.max_retries = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "operation": self.operation,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count
        }

class TaskManager:
    """Manages async background tasks with queue and status tracking"""
    
    # Operation handlers registry
    OPERATIONS = {}
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue: List[Task] = []
        self.tasks: Dict[str, Task] = {}
        self.workers_active = 0
        self.worker_tasks: List[asyncio.Task] = []
    
    @classmethod
    def register_operation(cls, operation_name: str) -> Callable:
        """Decorator to register async operation handler"""
        def decorator(func: Callable) -> Callable:
            cls.OPERATIONS[operation_name] = func
            logger.info(f"Registered operation handler: {operation_name}")
            return func
        return decorator
    
    def create_task(self, operation: str, data: Dict[str, Any], 
                   priority: int = 5, task_id: Optional[str] = None) -> str:
        """Create and queue a new async task"""
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        task = Task(task_id, operation, data, priority)
        self.task_queue.append(task)
        self.tasks[task_id] = task
        
        # Sort by priority (higher priority first)
        self.task_queue.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Task created: {task_id} (operation: {operation}, priority: {priority})")
        return task_id
    
    async def process_queue(self):
        """Process task queue with worker pool"""
        while True:
            try:
                # Fill worker pool while tasks are available
                while len(self.worker_tasks) < self.max_workers and self.task_queue:
                    task = self.task_queue.pop(0)
                    worker = asyncio.create_task(self._execute_task(task))
                    self.worker_tasks.append(worker)
                
                # Remove completed tasks
                self.worker_tasks = [t for t in self.worker_tasks if not t.done()]
                
                # Wait a bit before next iteration
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Task queue processing error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: Task):
        """Execute a single task with retry logic"""
        try:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            logger.info(f"Task started: {task.task_id}")
            
            # Get operation handler
            if task.operation not in self.OPERATIONS:
                raise ValueError(f"Unknown operation: {task.operation}")
            
            handler = self.OPERATIONS[task.operation]
            
            # Execute with retry logic
            while task.retry_count <= task.max_retries:
                try:
                    result = await handler(task.data)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    duration = (task.completed_at - task.started_at).total_seconds()
                    logger.info(f"Task completed: {task.task_id} ({duration:.2f}s)")
                    return
                except Exception as e:
                    task.retry_count += 1
                    if task.retry_count > task.max_retries:
                        raise
                    logger.warning(f"Task retry {task.retry_count}/{task.max_retries}: {task.task_id}")
                    await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Task failed: {task.task_id} - {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """Get all tasks, optionally filtered by status"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [t.to_dict() for t in tasks]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            if task in self.task_queue:
                self.task_queue.remove(task)
            logger.info(f"Task cancelled: {task_id}")
            return True
        return False
    
    def cleanup_old_tasks(self, hours: int = 24):
        """Remove tasks older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        to_remove = [
            task_id for task_id, task in self.tasks.items()
            if task.completed_at and task.completed_at < cutoff
        ]
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old tasks")
        return len(to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics"""
        tasks = list(self.tasks.values())
        return {
            "total_tasks": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "processing": len([t for t in tasks if t.status == TaskStatus.PROCESSING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "queue_length": len(self.task_queue),
            "worker_count": len([t for t in self.worker_tasks if not t.done()])
        }

# Global task manager instance
_task_manager: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    """Get or create global task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(max_workers=int(os.getenv("TASK_WORKERS", "4")))
    return _task_manager

# Example operation handlers (Phase 2.6)

@TaskManager.register_operation("video_analysis")
async def handle_video_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Background video analysis task"""
    logger.info(f"Starting video analysis for: {data.get('video_id')}")
    # Simulate long-running operation
    await asyncio.sleep(2)
    return {
        "video_id": data.get('video_id'),
        "frames_processed": 1200,
        "accuracy": 0.964,
        "timestamp": datetime.now().isoformat()
    }

@TaskManager.register_operation("report_generation")
async def handle_report_generation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Background report generation task"""
    logger.info(f"Generating report for user: {data.get('user_id')}")
    await asyncio.sleep(1.5)
    return {
        "user_id": data.get('user_id'),
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.now().isoformat()
    }

@TaskManager.register_operation("data_export")
async def handle_data_export(data: Dict[str, Any]) -> Dict[str, Any]:
    """Background data export task"""
    logger.info(f"Exporting data for user: {data.get('user_id')}")
    await asyncio.sleep(1)
    return {
        "user_id": data.get('user_id'),
        "export_format": data.get('format', 'csv'),
        "file_size_mb": 15.3,
        "download_url": f"/downloads/{uuid.uuid4()}.csv"
    }
