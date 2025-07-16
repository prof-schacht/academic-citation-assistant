"""API dependencies."""
from uuid import UUID, uuid4
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User


# Temporary test user ID (same as used in documents API)
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """
    Get the current authenticated user.
    
    This is a temporary implementation that returns a test user.
    In production, this should validate JWT tokens and return the actual user.
    """
    # For now, create or get a test user
    result = await db.execute(select(User).filter(User.id == TEST_USER_ID))
    test_user = result.scalar_one_or_none()
    
    if not test_user:
        # Create test user if it doesn't exist
        test_user = User(
            id=TEST_USER_ID,
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
            full_name="Test User",
            is_active=True,
            is_superuser=True  # Make test user a superuser for now
        )
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)
    
    return test_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not enough permissions"
        )
    return current_user