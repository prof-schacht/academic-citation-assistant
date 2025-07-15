"""Utilities for integrating system logging into services."""
from typing import Optional, Dict, Any
from uuid import UUID
from functools import wraps
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.logging_service import LoggingService
from app.models.system_log import LogLevel, LogCategory


def log_service_action(
    category: LogCategory,
    entity_type: Optional[str] = None,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Decorator for logging service actions.
    
    Args:
        category: The log category
        entity_type: The type of entity being processed
        success_message: Message template for successful operations
        error_message: Message template for failed operations
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract common parameters
            self = args[0] if args else None
            db = getattr(self, 'db', None)
            user_id = getattr(self, 'user_id', None)
            
            # Try to extract entity_id from kwargs or args
            entity_id = kwargs.get('paper_id') or kwargs.get('document_id') or \
                       kwargs.get('library_id') or kwargs.get('sync_id')
            
            if isinstance(entity_id, UUID):
                entity_id = str(entity_id)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success if we have a database session
                if db and success_message:
                    await log_async_info(
                        db, category, success_message.format(
                            entity_id=entity_id,
                            result=result
                        ),
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                
                return result
                
            except Exception as e:
                # Log error if we have a database session
                if db and error_message:
                    await log_async_error(
                        db, category, error_message.format(
                            entity_id=entity_id,
                            error=str(e)
                        ),
                        e,
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract common parameters
            self = args[0] if args else None
            db = getattr(self, 'db', None)
            user_id = getattr(self, 'user_id', None)
            
            # Try to extract entity_id from kwargs or args
            entity_id = kwargs.get('paper_id') or kwargs.get('document_id') or \
                       kwargs.get('library_id') or kwargs.get('sync_id')
            
            if isinstance(entity_id, UUID):
                entity_id = str(entity_id)
            
            try:
                result = func(*args, **kwargs)
                
                # Log success if we have a database session
                if db and success_message:
                    log_info(
                        db, category, success_message.format(
                            entity_id=entity_id,
                            result=result
                        ),
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                
                return result
                
            except Exception as e:
                # Log error if we have a database session
                if db and error_message:
                    log_error(
                        db, category, error_message.format(
                            entity_id=entity_id,
                            error=str(e)
                        ),
                        e,
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_info(
    db: Session,
    category: LogCategory,
    message: str,
    user_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None
):
    """Log an info message synchronously."""
    try:
        logging_service = LoggingService(db)
        logging_service.log_info(
            category=category,
            message=message,
            user_id=user_id,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id
        )
    except Exception as e:
        # Don't let logging failures break the application
        print(f"Failed to log info: {e}")


def log_error(
    db: Session,
    category: LogCategory,
    message: str,
    error: Exception,
    user_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None
):
    """Log an error message synchronously."""
    try:
        logging_service = LoggingService(db)
        logging_service.log_error(
            category=category,
            message=message,
            error=error,
            user_id=user_id,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id
        )
    except Exception as e:
        # Don't let logging failures break the application
        print(f"Failed to log error: {e}")


async def log_async_info(
    db: AsyncSession,
    category: LogCategory,
    message: str,
    user_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None
):
    """Log an info message asynchronously."""
    # For async sessions, we need to handle this differently
    # Create a sync session temporarily for logging
    from app.db.session import SessionLocal
    
    sync_db = SessionLocal()
    try:
        logging_service = LoggingService(sync_db)
        logging_service.log_info(
            category=category,
            message=message,
            user_id=user_id,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id
        )
        sync_db.commit()
    except Exception as e:
        sync_db.rollback()
        print(f"Failed to log async info: {e}")
    finally:
        sync_db.close()


async def log_async_error(
    db: AsyncSession,
    category: LogCategory,
    message: str,
    error: Exception,
    user_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None
):
    """Log an error message asynchronously."""
    # For async sessions, we need to handle this differently
    # Create a sync session temporarily for logging
    from app.db.session import SessionLocal
    
    sync_db = SessionLocal()
    try:
        logging_service = LoggingService(sync_db)
        logging_service.log_error(
            category=category,
            message=message,
            error=error,
            user_id=user_id,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id
        )
        sync_db.commit()
    except Exception as e:
        sync_db.rollback()
        print(f"Failed to log async error: {e}")
    finally:
        sync_db.close()