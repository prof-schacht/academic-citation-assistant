"""Test the logging system functionality."""
import asyncio
import os
from datetime import datetime
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.services.logging_service import LoggingService
from app.models.system_log import LogLevel, LogCategory


def test_logging_sync():
    """Test synchronous logging."""
    # Create sync engine and session
    sync_engine = create_engine(settings.database_url.replace("postgresql+asyncpg", "postgresql"))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db = SessionLocal()
    try:
        logging_service = LoggingService(db)
        
        # Test info log
        info_log = logging_service.log_info(
            category=LogCategory.SYSTEM,
            message="Test info log message",
            details={"test_key": "test_value"}
        )
        print(f"Created info log: {info_log.id}")
        
        # Test warning log
        warning_log = logging_service.log_warning(
            category=LogCategory.ZOTERO_SYNC,
            message="Test warning about sync",
            details={"papers_count": 0}
        )
        print(f"Created warning log: {warning_log.id}")
        
        # Test error log
        try:
            raise ValueError("Test error for logging")
        except Exception as e:
            error_log = logging_service.log_error(
                category=LogCategory.PDF_PROCESSING,
                message="Test error during PDF processing",
                error=e,
                entity_type="paper",
                entity_id="test-paper-123"
            )
            print(f"Created error log: {error_log.id}")
        
        # Test log retrieval
        from app.schemas.system_log import SystemLogFilter
        
        filter_params = SystemLogFilter(category=LogCategory.PDF_PROCESSING)
        logs, total = logging_service.get_logs(filter_params, page=1, per_page=10)
        
        print(f"\nFound {total} PDF processing logs:")
        for log in logs:
            print(f"  - [{log.level}] {log.message[:50]}...")
        
        # Test log statistics
        stats = logging_service.get_log_stats(days=1)
        print(f"\nLog statistics (last 24 hours):")
        print(f"  Total logs: {stats['total']}")
        print(f"  By level: {stats['by_level']}")
        print(f"  By category: {stats['by_category']}")
        
    finally:
        db.close()


async def test_logging_async():
    """Test asynchronous logging from services."""
    from app.db.session import AsyncSessionLocal
    from app.utils.logging_utils import log_async_info, log_async_error
    
    async with AsyncSessionLocal() as db:
        # Test async info log
        await log_async_info(
            db,
            LogCategory.ZOTERO_SYNC,
            "Test async Zotero sync started",
            details={"collections": ["ABC123", "DEF456"]}
        )
        print("Created async info log")
        
        # Test async error log
        try:
            raise FileNotFoundError("Test file not found: /path/to/missing.pdf")
        except Exception as e:
            await log_async_error(
                db,
                LogCategory.PDF_PROCESSING,
                "Test async PDF processing failed",
                e,
                entity_type="paper",
                entity_id="async-test-paper-456"
            )
            print("Created async error log")


def main():
    """Run all tests."""
    print("Testing Logging System\n" + "="*50)
    
    print("\n1. Testing synchronous logging:")
    test_logging_sync()
    
    print("\n2. Testing asynchronous logging:")
    asyncio.run(test_logging_async())
    
    print("\n✅ All logging tests completed!")


if __name__ == "__main__":
    main()