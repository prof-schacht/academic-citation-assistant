"""Simplified API endpoints for system logs without authentication."""
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db
from app.models.system_log import SystemLog, LogLevel, LogCategory
from app.schemas.system_log import SystemLogList

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
) -> SystemLogList:
    """Get paginated system logs."""
    
    # Build query
    query = select(SystemLog)
    
    # Apply filters
    filters = []
    if level:
        filters.append(SystemLog.level == level)
    if category:
        filters.append(SystemLog.category == category)
    if user_id:
        filters.append(SystemLog.user_id == user_id)
    if entity_type:
        filters.append(SystemLog.entity_type == entity_type)
    if entity_id:
        filters.append(SystemLog.entity_id == entity_id)
    if start_date:
        filters.append(SystemLog.created_at >= start_date)
    if end_date:
        filters.append(SystemLog.created_at <= end_date)
    if search:
        filters.append(SystemLog.message.ilike(f"%{search}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by created_at descending
    query = query.order_by(SystemLog.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(SystemLog)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    # Convert to response format
    log_list = []
    for log in logs:
        log_dict = {
            "id": str(log.id),
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "details": log.details,
            "error_trace": log.error_trace,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "created_at": log.created_at,
            "user_id": str(log.user_id) if log.user_id else None,
            "user_email": None  # TODO: Join with user table when needed
        }
        log_list.append(log_dict)
    
    return SystemLogList(
        logs=log_list,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/stats")
async def get_log_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days for statistics"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get log statistics."""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get counts by level
    level_stats_query = select(
        SystemLog.level,
        func.count(SystemLog.id).label('count')
    ).where(
        SystemLog.created_at >= start_date
    ).group_by(SystemLog.level)
    
    level_result = await db.execute(level_stats_query)
    level_stats = {row.level: row.count for row in level_result}
    
    # Get counts by category
    category_stats_query = select(
        SystemLog.category,
        func.count(SystemLog.id).label('count')
    ).where(
        SystemLog.created_at >= start_date
    ).group_by(SystemLog.category)
    
    category_result = await db.execute(category_stats_query)
    category_stats = {row.category: row.count for row in category_result}
    
    # Get total count
    total_query = select(func.count(SystemLog.id)).where(
        SystemLog.created_at >= start_date
    )
    total_result = await db.execute(total_query)
    total_count = total_result.scalar()
    
    return {
        "days": days,
        "total_logs": total_count,
        "by_level": level_stats,
        "by_category": category_stats,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat()
    }


@router.delete("/old")
async def delete_old_logs(
    days: int = Query(30, ge=1, description="Delete logs older than this many days"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete old logs."""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Delete old logs
    delete_query = delete(SystemLog).where(SystemLog.created_at < cutoff_date)
    result = await db.execute(delete_query)
    await db.commit()
    
    deleted_count = result.rowcount
    
    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} logs older than {days} days"
    }