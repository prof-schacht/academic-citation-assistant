"""Authentication dependencies."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from app.models import User
import uuid

# TODO: Implement proper authentication
# For now, return a mock user
async def get_current_user() -> User:
    """Get the current authenticated user."""
    # Mock user for development
    # In production, this would validate JWT tokens
    # Use the test user UUID that should exist in the database
    mock_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@example.com",
        full_name="Test User"
    )
    return mock_user