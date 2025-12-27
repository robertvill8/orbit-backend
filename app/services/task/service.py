"""
Task service for managing task lifecycle.
Handles CRUD operations, filtering, and business logic.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilters

logger = get_logger(__name__)


class TaskService:
    """
    Service for task management operations.

    Handles:
    - Task creation, retrieval, updating, deletion
    - Task filtering and search
    - Task status transitions
    - Business rule validation
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        task_data: TaskCreate,
        user_id: UUID,
        session_id: Optional[UUID] = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            task_data: Task creation data
            user_id: User ID who owns the task
            session_id: Optional session ID for context

        Returns:
            Created task instance
        """
        task = Task(
            user_id=user_id,
            session_id=session_id,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            metadata=task_data.metadata or {},
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        logger.info(
            "task_created",
            task_id=task.id,
            user_id=user_id,
            title=task.title,
        )

        return task

    async def get_task(self, task_id: UUID, user_id: UUID) -> Optional[Task]:
        """
        Get single task by ID.

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            Task instance or None if not found
        """
        result = await self.db.execute(
            select(Task).where(
                and_(Task.id == task_id, Task.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        user_id: UUID,
        filters: Optional[TaskFilters] = None,
    ) -> List[Task]:
        """
        Get tasks with optional filtering.

        Args:
            user_id: User ID
            filters: Optional filters (status, priority, date range, etc.)

        Returns:
            List of tasks matching filters
        """
        query = select(Task).where(Task.user_id == user_id)

        if filters:
            if filters.status:
                query = query.where(Task.status == filters.status)

            if filters.priority:
                query = query.where(Task.priority == filters.priority)

            if filters.due_date_from:
                query = query.where(Task.due_date >= filters.due_date_from)

            if filters.due_date_to:
                query = query.where(Task.due_date <= filters.due_date_to)

            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    Task.title.ilike(search_term) | Task.description.ilike(search_term)
                )

            # Pagination
            if filters.limit:
                query = query.limit(filters.limit)
            if filters.offset:
                query = query.offset(filters.offset)

        # Default sorting: most recent first
        query = query.order_by(Task.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task(
        self,
        task_id: UUID,
        task_data: TaskUpdate,
        user_id: UUID,
    ) -> Optional[Task]:
        """
        Update an existing task.

        Args:
            task_id: Task ID
            task_data: Updated task data
            user_id: User ID (for authorization)

        Returns:
            Updated task or None if not found
        """
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        # Update only provided fields
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        logger.info(
            "task_updated",
            task_id=task_id,
            user_id=user_id,
            updated_fields=list(update_data.keys()),
        )

        return task

    async def complete_task(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> Optional[Task]:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            Updated task or None if not found
        """
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        task.status = "completed"
        task.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(task)

        logger.info(
            "task_completed",
            task_id=task_id,
            user_id=user_id,
        )

        return task

    async def delete_task(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a task (hard delete).

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        task = await self.get_task(task_id, user_id)
        if not task:
            return False

        await self.db.delete(task)
        await self.db.commit()

        logger.info(
            "task_deleted",
            task_id=task_id,
            user_id=user_id,
        )

        return True

    async def get_task_count(
        self,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> int:
        """
        Get count of tasks, optionally filtered by status.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Task count
        """
        query = select(func.count(Task.id)).where(Task.user_id == user_id)

        if status:
            query = query.where(Task.status == status)

        result = await self.db.execute(query)
        return result.scalar_one()
