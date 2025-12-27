"""Activity log endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.logging import get_logger
from app.db.base import get_db

router = APIRouter()
logger = get_logger(__name__)


@router.post("/activities", status_code=status.HTTP_201_CREATED)
async def create_activity(db: AsyncSession = Depends(get_db)):
    """Log a new activity (typically called by internal services)."""
    logger.info("create_activity_called")
    # TODO: Implement activity creation logic
    return {
        "success": True,
        "data": {
            "id": "activity_xyz789",
            "activity_type": "task_created",
            "message": "Activity creation endpoint - Implementation pending"
        }
    }


@router.get("/activities")
async def list_activities(
    activity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List activities with filters and pagination."""
    logger.info("list_activities_called", activity_type=activity_type, page=page)
    # TODO: Implement activity listing logic
    return {
        "success": True,
        "data": [],
        "meta": {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
            }
        }
    }


@router.get("/activities/{activity_id}")
async def get_activity(activity_id: str, db: AsyncSession = Depends(get_db)):
    """Get activity details by ID."""
    logger.info("get_activity_called", activity_id=activity_id)
    # TODO: Implement activity retrieval logic
    return {
        "success": True,
        "data": {
            "id": activity_id,
            "message": "Activity retrieval endpoint - Implementation pending"
        }
    }


@router.get("/activities/types")
async def get_activity_types(db: AsyncSession = Depends(get_db)):
    """List available activity types and their schemas."""
    logger.info("get_activity_types_called")
    # TODO: Implement activity types logic
    return {
        "success": True,
        "data": [
            {
                "type": "email_read",
                "description": "Agent read an email from inbox",
                "metadata_schema": {}
            }
        ]
    }


@router.get("/activities/search")
async def search_activities(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Full-text search across activities."""
    logger.info("search_activities_called", query=q, page=page)
    # TODO: Implement activity search logic
    return {
        "success": True,
        "data": [],
        "meta": {
            "search_query": q,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 0,
            }
        }
    }
