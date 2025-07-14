"""Authentication dependencies."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from app.models import User

# TODO: Implement proper authentication
# For now, return a mock user
async def get_current_user() -> User:
    """Get the current authenticated user."""
    # Mock user for development
    # In production, this would validate JWT tokens
    mock_user = User(
        id="test-user",
        email="test@example.com",
        full_name="Test User"
    )
    return mock_user