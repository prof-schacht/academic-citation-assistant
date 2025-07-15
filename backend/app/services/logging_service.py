"""Logging service for creating and managing system logs."""
import traceback
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from sqlalchemy.sql import func

from app.models.system_log import SystemLog, LogLevel, LogCategory
from app.schemas.system_log import SystemLogCreate, SystemLogFilter


class LoggingService:
    """Service for managing system logs."""
    
    def __init__(self, db: Session):
        """Initialize logging service."""
        self.db = db
    
    def create_log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        user_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        error_trace: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        auto_commit: bool = True
    ) -> SystemLog:
        """Create a new system log entry."""
        log = SystemLog(
            level=level,
            category=category,
            message=message,
            user_id=user_id,
            details=details,
            error_trace=error_trace,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        self.db.add(log)
        
        if auto_commit:
            try:
                self.db.commit()
                self.db.refresh(log)
            except Exception:
                self.db.rollback()
                # If we can't log to DB, at least print to console
                print(f"[{level}] {category}: {message}")
                raise
        
        return log
    
    def log_error(
        self,
        category: LogCategory,
        message: str,
        error: Exception,
        user_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> SystemLog:
        """Log an error with traceback."""
        error_trace = traceback.format_exc()
        
        if details is None:
            details = {}
        
        details["error_type"] = type(error).__name__
        details["error_message"] = str(error)
        
        return self.create_log(
            level=LogLevel.ERROR,
            category=category,
            message=message,
            user_id=user_id,
            details=details,
            error_trace=error_trace,
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    def log_info(
        self,
        category: LogCategory,
        message: str,
        user_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> SystemLog:
        """Log an info message."""
        return self.create_log(
            level=LogLevel.INFO,
            category=category,
            message=message,
            user_id=user_id,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    def log_warning(
        self,
        category: LogCategory,
        message: str,
        user_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> SystemLog:
        """Log a warning message."""
        return self.create_log(
            level=LogLevel.WARNING,
            category=category,
            message=message,
            user_id=user_id,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    def get_logs(
        self,
        filter_params: SystemLogFilter,
        page: int = 1,
        per_page: int = 50
    ) -> tuple[list[SystemLog], int]:
        """Get filtered logs with pagination."""
        query = self.db.query(SystemLog)
        
        # Apply filters
        if filter_params.level:
            query = query.filter(SystemLog.level == filter_params.level)
        
        if filter_params.category:
            query = query.filter(SystemLog.category == filter_params.category)
        
        if filter_params.user_id:
            query = query.filter(SystemLog.user_id == filter_params.user_id)
        
        if filter_params.entity_type:
            query = query.filter(SystemLog.entity_type == filter_params.entity_type)
        
        if filter_params.entity_id:
            query = query.filter(SystemLog.entity_id == filter_params.entity_id)
        
        if filter_params.start_date:
            query = query.filter(SystemLog.created_at >= filter_params.start_date)
        
        if filter_params.end_date:
            query = query.filter(SystemLog.created_at <= filter_params.end_date)
        
        if filter_params.search:
            search_term = f"%{filter_params.search}%"
            query = query.filter(SystemLog.message.ilike(search_term))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        query = query.order_by(desc(SystemLog.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        logs = query.all()
        
        return logs, total
    
    def delete_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = self.db.query(SystemLog).filter(
            SystemLog.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return deleted_count
    
    def get_log_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get log statistics for the specified number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count by level
        level_counts = dict(
            self.db.query(SystemLog.level, func.count(SystemLog.id))
            .filter(SystemLog.created_at >= cutoff_date)
            .group_by(SystemLog.level)
            .all()
        )
        
        # Count by category
        category_counts = dict(
            self.db.query(SystemLog.category, func.count(SystemLog.id))
            .filter(SystemLog.created_at >= cutoff_date)
            .group_by(SystemLog.category)
            .all()
        )
        
        # Total count
        total_count = self.db.query(func.count(SystemLog.id)).filter(
            SystemLog.created_at >= cutoff_date
        ).scalar()
        
        return {
            "total": total_count,
            "by_level": level_counts,
            "by_category": category_counts,
            "period_days": days
        }


# Import timedelta at the top
from datetime import timedelta