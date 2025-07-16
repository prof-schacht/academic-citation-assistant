"""API endpoints for system logs."""
from typing import Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.system_log import LogLevel, LogCategory
from app.schemas.system_log import SystemLog, SystemLogList, SystemLogFilter
from app.services.logging_service import LoggingService

router = APIRouter()


@router.get("/", response_model=SystemLogList)
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    category: Optional[LogCategory] = Query(None, description="Filter by log category"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    search: Optional[str] = Query(None, description="Search in log messages"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SystemLogList:
    """
    Get paginated system logs.
    
    Only superusers can view all logs. Regular users can only view their own logs.
    """
    logging_service = LoggingService(db)
    
    # Create filter object
    filter_params = SystemLogFilter(
        level=level,
        category=category,
        user_id=user_id if current_user.is_superuser else current_user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        search=search
    )
    
    # Get filtered logs
    logs, total = logging_service.get_logs(filter_params, page, per_page)
    
    # Convert to response schema
    log_responses = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "details": log.details,
            "error_trace": log.error_trace,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "created_at": log.created_at,
            "user_id": log.user_id,
            "user_email": log.user.email if log.user else None
        }
        log_responses.append(SystemLog(**log_dict))
    
    total_pages = (total + per_page - 1) // per_page
    
    return SystemLogList(
        logs=log_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/stats")
async def get_log_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days for statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get log statistics.
    
    Only available to superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    logging_service = LoggingService(db)
    return logging_service.get_log_stats(days)


@router.delete("/old")
async def delete_old_logs(
    days: int = Query(30, ge=1, description="Delete logs older than this many days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Delete old logs.
    
    Only available to superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    logging_service = LoggingService(db)
    deleted_count = logging_service.delete_old_logs(days)
    
    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} logs older than {days} days"
    }